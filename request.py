from dotenv import dotenv_values
from utils import base64_encoding
import requests as req
import os, json

if not os.path.isfile('.env'):
    print('Error! the .env setting is missing.')
    quit()

config = dotenv_values(".env")
credential = f"{config['API_USERNAME']}:{config['API_PASSWORD']}"
admin_headers = {
    'Authorization': f'Basic {base64_encoding(credential)}'
}

try:
    check_login_res = req.get(f'{config["API_HOST"]}/api/v4/user', headers=admin_headers)
    if check_login_res.status_code != 200:
        print('Wrong username or password! please check your .env settings.')
        quit()

    login_user = json.loads(check_login_res.text)
    if 'api_reader' not in login_user['roles']:
        print('This user missing "api_reader" permission.')
        quit()

except req.exceptions.RequestException as e:
    print('API_HOST error! please check your .env settings.')
    quit()


def get(uri, headers=admin_headers):
    res = req.get(f'{config["API_HOST"]}/{uri}', headers=headers)
    return json.loads(res.text)
