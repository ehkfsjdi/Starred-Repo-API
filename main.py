# An application for fecthing the starred repositories of an authenticated user
# Used https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps to implement the authentication behavior
# Used https://stackoverflow.com/questions/72975593/where-to-store-tokens-secrets-with-fastapi-python for using a session to store the access token
# Secret handling was modeled after: https://blog.gitguardian.com/how-to-handle-secrets-in-python/

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import httpx
from utils import get_csrf_token, format_repo_list
import uuid
from dotenv import dotenv_values
import time

# Get secrets from the environment file
secrets = dotenv_values(".env")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=uuid.uuid4())

# Get the root of the application
@app.get("/")
async def read_root():
    return {"Message": "API for fetching GitHub starred repositories"}

# GitHub authentication
# Used https://medium.com/@tony.infisical/guide-to-using-oauth-2-0-to-access-github-api-818383862591 to get a better idea of the use of parameters
# Used https://fastapi.tiangolo.com/es/advanced/custom-response/ to get the redirection right
@app.get("/login/browser", response_class=RedirectResponse)
async def authorize(request: Request, login: str = '', signup: str = 'true',
                    scope: list[str] = ['repo']):
    '''Authorize the application using web browser'''

    # Get the user's GitHub identity
    auth_url = 'https://github.com/login/oauth/authorize/'
    # Save the CSRF token to the session backend
    state = get_csrf_token()
    request.session['state'] = state
    params = {'scope': scope, 'client_id': secrets['CLIENT_ID'], 
              'redirect_uri': secrets['REDIRECT_URI'], 'allow_signup': signup,  
              'state': state, 'response_type': 'code', 'login': login}

    # Do the get request
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(auth_url, params=params)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=500, detail=f'{exc}')

    return RedirectResponse(res.headers['location'])


@app.get("/login/cli", response_class=RedirectResponse)
async def authorize(scope = 'repo'):
    '''Authorize the application using cli'''

    # Get the user's GitHub identity
    auth_url = 'https://github.com/login/device/code'
    header = {'Accept': 'application/json'}
    data = {'scope': scope, 'client_id': secrets['CLIENT_ID']}
    
    # Request the code and url for verification from GitHub
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(auth_url, data=data, headers=header)
            res.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=500, detail=str(exc))
    
    result = res.json()

    return RedirectResponse(f'/poll?user_code={result["user_code"]}&verification_uri={result["verification_uri"]}&code={result["device_code"]}&interval={result["interval"]}&expires=5&message=Enter the user code in browser using the given verification url.')


# Used https://docs.github.com/en/rest/activity/starring?apiVersion=2022-11-28 for creating the query and choosing parameters
@app.get("/callback", response_class=RedirectResponse)
async def get_access_token(request: Request, code: str, state: str, 
                           accept_type: str = 'application/json'):
    '''Get the access token from GitHub in browser mode'''

    # Check that the CSRF token is unchanged
    if state != request.session.get('state'):
        # If the token is not unchanged, raise an error
        raise HTTPException(status_code=400, detail='Invalid CSRF token')
    
    # Exchange the received code for the access token
    access_url = 'https://github.com/login/oauth/access_token'
    access_url = 'https://?kjbad'
    header = {'Accept': accept_type}
    data = {'client_id': secrets['CLIENT_ID'], 'client_secret': secrets['CLIENT_SECRET'], 
            'code': code, 'redirect_uri': secrets['REDIRECT_URI']}
    
    # The post request
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(access_url, headers=header, data=data)
            result = res.json()
            res.raise_for_status()
            # Check if the code has expired or is wrong
            if "error" in result:
                return JSONResponse({'error': result["error"], 'detail': result["error_description"], 'Message': 'Return to /login/browser to get a new code.'})
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    # Save the access token into the session backend
    request.session['access_token'] = result['access_token']

    return RedirectResponse('/starred')


@app.get("/poll")
async def poll_access_token(request: Request, interval: int, expires: int, 
                            code: str, accept_type: str = 'application/json'):
    '''Poll for the access token from GitHub in cli mode'''

    # Exchange the received code for the access token
    access_url = 'https://github.com/login/oauth/access_token'
    grant_type = f'urn:ietf:params:oauth:grant-type:{code}'
    header = {'Accept': accept_type}
    data = {'client_id': secrets['CLIENT_ID'], 'device_code': code, 
            'grant_type': grant_type}
    print(request.session)
    
    # Start a timer
    start_time = time.time()
    # Poll for the access token
    async with httpx.AsyncClient() as client:
        while (time.time() - start_time) < expires:
            print(time.time() - start_time, expires)
            try:
                res = await client.post(access_url, headers=header, data=data)
                result = res.json()
                res.raise_for_status()
                print(res, result)
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=500, detail=str(exc))

            # If the result contains the access token, we can stop polling
            if 'access_token' in result:
                request.session['access_token'] = result['access_token']
                return RedirectResponse('/starred')

            # Sleep for the duration of the min polling interval
            time.sleep(interval)

    return {'Message': 'Credentials expired. Return to /login/cli to authorize again.'}


@app.get("/starred")
async def display_starred(request: Request, accept: str = 'application/vnd.github+json',
                          sort: str = 'created', direction: str = 'desc',
                          per_page: int = 30, page: int = 1):
    '''Display the list of repositories starred by the authenticated user'''

    # Get the starred repositories
    starred_url = 'https://api.github.com/user/starred'
    token = request.session.get('access_token')
    headers = {'Accept': accept, 'Authorization': f'Bearer {token}'}
    params = {'sort': sort, 'direction': direction, 
              'per_page': per_page, 'page': page}
    print(request.session)
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(starred_url, headers=headers, params=params)
            res.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    # Convert to json object
    result = res.json()
    # Get the number of starred repositories
    n_starred = len(result)

    # Modify the returned list of starred repositories to include only name, description, URL, license (if exists) and topics
    repo_list = format_repo_list(result)

    return {'n_starred_repos': n_starred, 'list_of_starred_repos': repo_list}

