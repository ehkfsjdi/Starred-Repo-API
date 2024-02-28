# Helper functions for the API
import secrets

def get_csrf_token():
    '''Create a random CSRF token'''
    return str(secrets.token_hex(32))

def format_repo_list(repos):
    '''Modify the format of repositories'''

    # Filter out all repositories that are private, i.e. have "private": true
    public_repos = [r for r in repos if r['private'] == False]
    # Remove all unnecessary information about the repositories
    modified_repos = [{'name': i['name'], 'description': i['description'], 'url': i['url'], 'license': i['license'], 'topics': i['topics']} if i['license'] is not None else {'name': i['name'], 'description': i['description'], 'url': i['url'], 'topics': i['topics']} for i in public_repos]

    return modified_repos
