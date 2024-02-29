# Test the API
# Used https://fastapi.tiangolo.com/tutorial/testing/#extended-testing-file for the testing tools and framework

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_main():
    '''Test the root get function'''
    response = client.get("http://127.0.0.1:8000/")
    assert response.status_code == 200
    assert response.json() == {"Message": "API for fetching GitHub starred repositories"}

def test_authorize_browser():
    '''Test GitHub authorization browser mode'''
    response = client.get("/login/browser")
    # Returns an 404 Not found error due to redirect
    assert response.is_error == True
    assert response.status_code == 404

def test_authorize_cli_false():
    '''Test GitHub authorization cli mode'''
    response = client.get("/login/cli/?scope=12563")
    print(response)
    assert response.is_error == True

def test_polling_expire():
    '''Test polling GitHub for the access token in cli mode'''
    response = client.get("/poll?code=gfuy4tgf43874uhf3874&interval=5&expires=1")
    assert response.json() == {'Message': 'Credentials expired. Return to /login/cli to authorize again.'}

def test_polling_error():
    '''Test polling GitHub for the access token in cli mode'''
    response = client.get("/poll/?code=gfuy4tgf43874uhf3874&interval=5&expires=5&accept_type=paper")
    assert response.is_error == True
    assert response.status_code == 500
    assert response.json() == {'detail': 'An error occurred'}

def test_callback_csrf_error():
    '''Test callback from GitHub when csrf token is not valid'''
    response = client.get("/callback?code=526r3fe25&state=jabhdvzjhgx")
    assert response.status_code == 400
    assert response.is_error == True
    assert response.json() == {'detail': 'Invalid CSRF token'}

def test_display_starred_false():
    '''Test displaying the starred repositories without authorization'''
    response = client.get("/starred")
    assert response.is_error == True
    assert response.status_code == 500
