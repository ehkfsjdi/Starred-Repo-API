# Test the API
# Used https://fastapi.tiangolo.com/tutorial/testing/#extended-testing-file for help with how to use the TestClient

from fastapi.testclient import TestClient
from main import app, request_token_device, poll_access_token
import asyncio
import pytest
import os

pytest_plugins = ('pytest_asyncio',)

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

@pytest.mark.asyncio
async def test_request_token_device_true():
    result = await request_token_device(code='hafdhg7635')
    assert type(result) == type({})
    assert result != None

def test_callback_csrf_error():
    '''Test callback from GitHub when csrf token is not valid'''
    response = client.get("/callback?code=526r3fe25&state=jabhdvzjhgx")
    assert response.status_code == 400
    assert response.is_error == True
    assert response.json() == {'detail': 'Invalid CSRF token'}

def test_display_starred_true():
    '''Test displaying the starred repositories'''
    # For this to work, the user needs to have authorized a short time ago, i.e., 
    # there needs to be a valid .token file
    response = client.get("/starred")
    assert response.status_code == 200

def test_display_starred_false():
    '''Test displaying the starred repositories without authorization'''
    if os.path.exists("./.token"):
        os.remove("./.token")
    response = client.get("/starred")
    assert response.is_error == True
    assert response.status_code == 500
