#!/usr/bin/env python3

import requests
import yaml
import os
import textwrap
import logging
import base64


class FitbitCredentialsError(Exception):
    pass


class FitbitApiError(Exception):
    pass


class FitbitTokenError(Exception):
    pass


class FitbitTokenExpiredError(Exception):
    pass


class FitbitClient:

    class UserCredentialKeys:
        CLIENT_ID = 'client_id'
        CLIENT_SECRET = 'client_secret'
        CODE = 'code'

    class Oauth2TokenKeys:
        ACCESS_TOKEN = 'access_token'
        REFRESH_TOKEN = 'refresh_token'
        SCOPE = 'scope'
        USER_ID = 'user_id'

    class FitbitApi:
        TOKEN_URL = "https://api.fitbit.com/oauth2/token"
        API_URL = "api.fitbit.com"
        CONTENT_TYPE = "application/x-www-form-urlencoded"
        ACCESS_GRANT_TYPE = "authorization_code"
        REFRESH_GRANT_TYPE = "refresh_token"
        EXPIRED_TOKEN_ERROR_TYPE = "expired_token"

    CREDENTIALS = [
        UserCredentialKeys.CLIENT_ID,
        UserCredentialKeys.CLIENT_SECRET,
        Oauth2TokenKeys.ACCESS_TOKEN,
        Oauth2TokenKeys.REFRESH_TOKEN,
        Oauth2TokenKeys.SCOPE,
        Oauth2TokenKeys.USER_ID,
    ]

    def __init__(
            self,
            credentials_file_path="fitbit_credentials.yaml",
            redirect_url="http://localhost",
    ):

        self._credentials_file_path = credentials_file_path
        self._redirect_url = redirect_url
        FitbitClient._init_credentials(self._credentials_file_path, self._redirect_url)

    def request_url(self, url):

        credentials = self._get_credentials(self._credentials_file_path, self._redirect_url)
        acccess_token = credentials[FitbitClient.Oauth2TokenKeys.ACCESS_TOKEN]

        try:
            response = FitbitClient._request_url(url, acccess_token)
        except FitbitTokenExpiredError:

            client_id = credentials[FitbitClient.UserCredentialKeys.CLIENT_ID]
            client_secret = credentials[FitbitClient.UserCredentialKeys.CLIENT_SECRET]
            refresh_token = credentials[FitbitClient.Oauth2TokenKeys.REFRESH_TOKEN]

            acccess_token = FitbitClient._renew_token(client_id, client_secret, refresh_token)
            credentials[FitbitClient.Oauth2TokenKeys.ACCESS_TOKEN] = acccess_token
            FitbitClient._save_dict_to_yaml(credentials, self._credentials_file_path)

            response = FitbitClient._request_url(url, acccess_token)

        return response

    @staticmethod
    def _request_url(url, authorization_token):
        response = requests.get(
            url=url,
            headers=FitbitClient._get_data_header(
                authorization_token=authorization_token
            )
        ).json()
        return response

    @staticmethod
    def _init_credentials(credentials_file_path, redirect_url):
        _ = FitbitClient._get_credentials(credentials_file_path, redirect_url)

    @staticmethod
    def _get_credentials(credentials_file_path, redirect_url):
        if os.path.exists(credentials_file_path):
            try:
                return FitbitClient._load_dict_from_yaml(credentials_file_path)
            except TypeError:
                pass

        client_id, client_secret, code = FitbitClient._input_user_credentials()
        user_credentials = {
            FitbitClient.UserCredentialKeys.CLIENT_ID: client_id,
            FitbitClient.UserCredentialKeys.CLIENT_SECRET: client_secret,
        }

        oauth_credentials = FitbitClient._init_token(
            client_id=client_id,
            client_secret=client_secret,
            code=code,
            redirect_url=redirect_url,
        )

        credentials = {**user_credentials, **oauth_credentials}
        FitbitClient._save_dict_to_yaml(credentials, credentials_file_path)

        return credentials

    @staticmethod
    def _init_token(client_id, client_secret, code, redirect_url):

        response = requests.post(
            FitbitClient.FitbitApi.TOKEN_URL,
            headers=FitbitClient._get_token_header(
                client_id,
                client_secret
            ),
            data=FitbitClient._get_data_for_init_token(
                client_id=client_id,
                redirect_url=redirect_url,
                code=code,
            ),
        ).json()

        try:
            FitbitClient._check_response_for_errors(response)
        except Exception as e:
            raise FitbitTokenError from e

        return FitbitClient._get_select_keys_if_they_exist(
            response,
            FitbitClient.CREDENTIALS,
        )

    @staticmethod
    def _renew_token(client_id, client_secret, refresh_token):
        response = requests.post(
            FitbitClient.FitbitApi.TOKEN_URL,
            headers=FitbitClient._get_token_header(
                client_id,
                client_secret
            ),
            data=FitbitClient._get_data_for_refresh_token(
                refresh_token=refresh_token,
            ),
        ).json()

        try:
            FitbitClient._check_response_for_errors(response)
        except Exception as e:
            raise FitbitTokenError from e

        return response[FitbitClient.Oauth2TokenKeys.ACCESS_TOKEN]

    @staticmethod
    def _get_select_keys_if_they_exist(dictionary, select_keys):
        return {key: dictionary[key] for key in dictionary if key in select_keys}

    @staticmethod
    def _input_user_credentials(
            client_id=None,
            client_secret=None,
            code=None,
    ):
        if client_id is None:
            client_id = input("Client ID: ")
        if client_secret is None:
            client_secret = input("Client Secret: ")
        if code is None:
            code = input("Code: ")

        return client_id, client_secret, code

    @staticmethod
    def _check_response_for_errors(response):
        response_ = response.copy()

        if type(response_) is not list:
            response_ = [response_]

        for r in response_:

            if type(r) is not dict:
                raise TypeError("response should be a dictionary or a list of dictionaries")

            if 'success' in r.keys():
                if r['success'] is False:
                    error_message = FitbitClient._get_error_message_from_get_response(response)
                    logging.error(error_message, exc_info=True)
                    if FitbitClient._is_access_token_expired(response):
                        raise FitbitTokenExpiredError(error_message)
                    else:
                        raise FitbitCredentialsError(error_message)

    @staticmethod
    def _is_access_token_expired(response):
        for e in response['errors']:
            if e["errorType"] == FitbitClient.FitbitApi.EXPIRED_TOKEN_ERROR_TYPE:
                return True

    @staticmethod
    def _get_error_message_from_get_response(response):
        error_message = "\n"
        for e in response['errors']:
            error_message += "\t{}:\n".format(e["errorType"]) + textwrap.indent(
                textwrap.fill(e['message']), prefix='\t\t'
            ) + "\n"
        return error_message

    @staticmethod
    def _save_dict_to_yaml(dictionary, file_path):
        with open(file_path, 'w') as f:
            yaml.dump(dictionary, f)

    @staticmethod
    def _load_dict_from_yaml(file_path):
        with open(file_path, 'r') as f:
            return yaml.load(f, Loader=yaml.FullLoader)

    @staticmethod
    def _get_token_header(client_id, client_secret):
        return {
            'Authorization': 'Basic {}'.format(
                FitbitClient._get_authorization(client_id, client_secret)
            ),
            'Content-Type': FitbitClient.FitbitApi.CONTENT_TYPE,
        }

    @staticmethod
    def _get_data_header(authorization_token):
        return {
            'Authorization': 'Bearer {}'.format(authorization_token),
        }

    @staticmethod
    def _get_data_for_init_token(client_id, redirect_url, code):
        return {
            "clientId": client_id,
            "grant_type": FitbitClient.FitbitApi.ACCESS_GRANT_TYPE,
            "redirect_uri": redirect_url,
            "code": code,
        }

    @staticmethod
    def _get_data_for_refresh_token(refresh_token):
        return {
            "refresh_token": refresh_token,
            "grant_type": FitbitClient.FitbitApi.REFRESH_GRANT_TYPE,
        }

    @staticmethod
    def _get_authorization(client_id, client_secret):
        format_ = "utf-8"
        return base64.b64encode(
            "{id}:{secret}".format(
                id=client_id,
                secret=client_secret
            ).encode(format_)
        ).decode(format_)
