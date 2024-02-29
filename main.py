# An application for fecthing the starred repositories of an authenticated user
# Used https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps to implement the authentication behavior
# Used https://stackoverflow.com/questions/72975593/where-to-store-tokens-secrets-with-fastapi-python for using a session to store the access token
# Secret handling was modeled after: https://blog.gitguardian.com/how-to-handle-secrets-in-python/

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import httpx
from utils import get_csrf_token, format_repo_list, write_token
import uuid
from dotenv import dotenv_values
import time
import os

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


#@app.get("/login/cli", response_class=RedirectResponse)
@app.get("/login/cli")
async def authorize(background_tasks: BackgroundTasks, 
                    scope: str = 'repo'):
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

    # Start a background task that polls GitHub for the access token
    # This: https://fastapi.tiangolo.com/tutorial/background-tasks/ was used to determine how to use background tasks
    background_tasks.add_task(poll_access_token, code=result["device_code"], interval=result["interval"])
    
    return {'Message': f'Please enter the user code: {result["user_code"]} to the verification url: {result["verification_uri"]} in a browser.'}


# Used https://docs.github.com/en/rest/activity/starring?apiVersion=2022-11-28 for creating the query and choosing parameters
#@app.get("/callback", response_class=Union[RedirectResponse, JSONResponse])
@app.get("/callback")
async def get_access_token(request: Request, code: str, state: str):
    '''Get the access token from GitHub in browser mode'''

    # Check that the CSRF token is unchanged
    if state != request.session.get('state'):
        # If the token is not unchanged, raise an error
        raise HTTPException(status_code=400, detail='Invalid CSRF token')
    
    # Exchange the received code for the access token
    access_url = 'https://github.com/login/oauth/access_token'
    header = {'Accept': 'application/json'}
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

    return JSONResponse({'Message': 'Authentication successful'})


async def request_token_device(code: str):
    '''Request the access token from GitHub using device flow.'''
    access_url = 'https://github.com/login/oauth/access_token'
    header = {'Accept': 'application/json'}
    data = {'client_id': secrets['CLIENT_ID'], 'device_code': code, 
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'}
    
    # Send POST request
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(access_url, headers=header, data=data)
            result = res.json()
            res.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        
    return result


# Used https://docs.github.com/en/apps/creating-github-apps/writing-code-for-a-github-app/building-a-cli-with-a-github-app#write-the-cli to figure out a working architecture for the polling
async def poll_access_token(interval: int, code: str):
    '''Poll for the access token from GitHub in cli mode'''
    
    #while True:
    while True:
        result = await request_token_device(code)

        # If the result contains the access token, we can stop polling
        if 'access_token' in result.keys():
            break
        # Otherwise there was an error response
        else:
            if result['error'] == 'authorization_pending':
                # Continue polling after the min interval, the user has not yet entered the code
                time.sleep(interval)
            elif result['error'] == 'slow_down':
                # Too fast polling, increase interval with 5 seconds
                time.sleep(interval + 5)
            elif result['error'] == 'expired_token':
                # The token has expired, restart authorization process
                print('Credentials expired. Return to /login/cli to authorize again.')
                return 1
            elif result['error'] == 'access_denied':
                # Process cancelled by user, stop
                print('Login process stopped by user.')
                return 1

    # Write the access token into a file
    write_token(result['access_token'])

    return 0


@app.get("/starred")
async def display_starred(request: Request, sort: str = 'created', 
                          direction: str = 'desc', per_page: int = 30, 
                          page: int = 1):
    '''Display the list of repositories starred by the authenticated user'''

    # If we have the access token in the session use it
    if request.session != {}:
        token = request.session.get('access_token')
    # Else, check if the token is stored in the .token file
    elif os. path. exists('./.token'):
        # Read the token
        f = open("./.token", "r")
        token = f.read()
    else:
        return {'error': 'You are missign the access token. Authorize again from /login/browser or /login/cli'}
    
    # Get the starred repositories
    starred_url = 'https://api.github.com/user/starred'
    headers = {'Accept': 'application/vnd.github+json', 
               'Authorization': f'Bearer {token}'}
    params = {'sort': sort, 'direction': direction, 
              'per_page': per_page, 'page': page}
    
    # Perform the GET request
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

