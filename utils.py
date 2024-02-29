# Helper functions for the API
import secrets
import os

def get_csrf_token():
    '''Create a random CSRF token'''
    return str(secrets.token_hex(32))

def write_token(token: str):
    # Write the access token into a file
    f = open("./.token", "w")
    f.write(token)
    f.close()
    # Change the file permissions to only read and write by owner
    # This: https://www.tutorialspoint.com/How-to-change-the-permission-of-a-file-using-Python was used to determine how to change file permissions
    os.chmod("./.token", 0o600)
    return

def format_repo_list(repos):
    '''Modify the format of repositories'''

    # Filter out all repositories that are private, i.e. have "private": true
    public_repos = [r for r in repos if r['private'] == False]
    # Remove all unnecessary information about the repositories
    modified_repos = [{'name': i['name'], 'description': i['description'], 'url': i['url'], 'license': i['license'], 'topics': i['topics']} for i in public_repos]

    return modified_repos
