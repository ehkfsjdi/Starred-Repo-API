# Starred-Repo-API
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


### Secrets
The secrets are in a environment file .env. You need to create your own env-file and have a running GitHub Oauth application to run the API.
The architecture of the env-file:
```
CLIENT_ID = 'your_client_id'
REDIRECT_URI = 'http://127.0.0.1:8000/callback'
CLIENT_SECRET = 'your_client_secret'
```

## Running the API
To run the application, type on command line:
uvicorn main:app --host 127.0.0.1 --port 8000

## Interacting with the API

### Browser Mode
The root url is: http://127.0.0.1:8000/
Navigate to http://127.0.0.1:8000/login/browser to login. 
Navigate to http://127.0.0.1:8000/starred to view the starred repositories.

### Cli Mode
To authenticate: curl -v http://localhost:8000/login/cli
Follow the instructions given to enter the user code in https://github.com/login/device.

To retrieve starred repositories after authentication: curl http://localhost:8000/starred

// PS. In cli mode, the token stays in memory until overwritten or the .token file is removed

## Testing
To test the application, run the tests using pytest with the following command:
pytest

// Make sure all the requirements for tests are fullfilled
