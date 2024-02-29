# Starred_Repo_API
An API for fetching the starred public GitHub repositories of an authenticated user.
The dependencies are in requirements.txt.
The API can be used with two modes: browser and cli.

## Configuration
The API has the following default configuration:
**Common:**
```
sort:      'created' How the results of the starred repository query are sorted. Options: created, updated.
direction: 'desc'    The direction of sorting. Options: asc, desc
per_page:  30        The number of results per page (max 100)
page:      1         The page number of the results to fetch.
```
**Only in browser mode:**
```
login:     ''        Specifies login.
scope:     ['repo']  The scopes of the query for the GitHub API.
signup:    'true'    Whether signing up to GitHub is allowed at authentication. Options: true, false
```
**Only in cli mode:**
```
scope:     'repo'    The scope of the query for the GitHub API.
```
The configuration can be changed by changing the aforementioned parameters in the API endpoint url, e.g.:
http://127.0.0.1:8000/login/browser?signup=false


**Secrets**
The secrets are in a environment file .env. You need to create your own env-file and have a running GitHub Oauth application to run the API.
The architecture of the env-file:
CLIENT_ID = '***'
REDIRECT_URI = 'http://127.0.0.1:8000/callback'
CLIENT_SECRET = '***'

## Running the API
To run the application, type on command line:
uvicorn main:app --host 127.0.0.1 --port 8000

## Interacting with the API

### Browser Mode
The root url is: http://127.0.0.1:8000/
Navigate to http://127.0.0.1:8000/login/browser to login. You'll be redirected to http://127.0.0.1:8000/starred where the starred repositories are displayed.

### Cli Mode
-----
To authenticate: curl -v http://localhost:8000/login/cli
The redirect includes an url of form 'http://localhost:8000/poll?user_code=...&verification_uri=https://github.com/login/device&code=...&interval=...&expires=...&message=Enter%20the%20user%20code%20in%20browser%20using%20the%20given%20verification%20url.'.
Visit the verification_uri (https://github.com/login/device) and type in the user code from the aforementioned redirection url.

To retrieve starred repositories: curl http://localhost:8000/starred
------


## Testing
To test the application, run the tests using pytest with the following command:
pytest
