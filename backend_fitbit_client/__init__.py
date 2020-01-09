#!/usr/bin/env python3

import requests
import yaml
import datetime
import os
import pandas
import textwrap
import logging


class FitbitCredentialsError(Exception):
    pass


class FitbitApiError(Exception):
    pass


class BackendFitbitClient:

    class Oauth2Fields:
        ACCESS_TOKEN = 'access_token'
        REFRESH_TOKEN = 'refresh_token'
        SCOPE = 'scope'
        USER_ID = 'user_id'

    class FitbitApi:
        TOKEN_URL = "https://api.fitbit.com/oauth2/token"
        API_URL = "api.fitbit.com"
        STEPS_RESOURCE_PATH = "activities/steps"
        STEPS_DETAIL_LEVEL_1_MIN = "1min"
        LAST_SYNC_KEY = "lastSyncTime"

    def __init__(
            self,
            fitbit_info_file: str = "fitbit_info.yaml",
            is_run_setup: bool = True,
            **kwargs,
    ):
        self._fitbit_info_file = fitbit_info_file

        self._access_token = None
        self._scope = None
        self._user_id = None

        if is_run_setup:
            self.setup_oaut2_fields(**kwargs)

    def setup_oaut2_fields(self, **kwargs):

        is_init_oauth2_token = True
        if os.path.exists(self._fitbit_info_file):
            try:
                self._load_oauth2_fields()
                is_init_oauth2_token = False
            except TypeError:
                pass

        if is_init_oauth2_token:
            self._init_oauth2_token(**kwargs)
            self._save_oauth2_fields()

    def _load_oauth2_fields(self):

        logging.info("Loading oauth2 fields")

        with open(self._fitbit_info_file, 'r') as f:

            content = yaml.load(f, Loader=yaml.FullLoader)
            self._access_token = content[self.Oauth2Fields.ACCESS_TOKEN]
            self._scope = content[self.Oauth2Fields.SCOPE]
            self._user_id = content[self.Oauth2Fields.USER_ID]

    def _save_oauth2_fields(self):

        assert self._access_token is not None

        logging.info("Saving oauth2 fields")

        with open(self._fitbit_info_file, 'w') as f:
            yaml.dump(
                {
                    self.Oauth2Fields.ACCESS_TOKEN: self._access_token,
                    self.Oauth2Fields.SCOPE: self._scope,
                    self.Oauth2Fields.USER_ID: self._user_id,
                },
                f
            )

    def _init_oauth2_token(
            self,
            client_id: str = None,
            code: str = None,
            authorization: str = None,
            redirect_url: str = "http://localhost",
    ):

        logging.info("Initializing oauth2 fields")

        if client_id is None:
            client_id = input("Client ID: ")
        if code is None:
            code = input("Code: ")
        if authorization is None:
            authorization = input("Authorization: ")

        headers = {
            'Authorization': 'Basic {}'.format(authorization),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            "clientId": client_id,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_url,
            "code": code,
        }

        response = requests.post(self.FitbitApi.TOKEN_URL, data=data, headers=headers).json()

        if 'success' in response.keys() and self.Oauth2Fields.ACCESS_TOKEN not in response.keys():
            if response['success'] is False:
                error_message = self._get_error_message_from_get_response(response)
                logging.error(error_message, exc_info=True)
                raise FitbitCredentialsError(error_message)
            else:
                error_message = "If successful, there should be a message, not a 'True' for 'success'"
                logging.error(error_message, exc_info=True)
                raise FitbitApiError(error_message)
        elif 'success' not in response.keys() and self.Oauth2Fields.ACCESS_TOKEN not in response.keys():
            error_message = "The Fitbit api isn't responding as it should - perhaps check your connection"
            logging.error(error_message, exc_info=True)
            raise ConnectionError(error_message)
        else:
            self._access_token = response[self.Oauth2Fields.ACCESS_TOKEN]
            self._scope = response[self.Oauth2Fields.SCOPE]
            self._user_id = response[self.Oauth2Fields.USER_ID]

    @staticmethod
    def _get_error_message_from_get_response(response):
        error_message = "\n"
        for e in response['errors']:
            error_message += "\t{}:\n".format(e["errorType"]) + textwrap.indent(
                textwrap.fill(e['message']), prefix='\t\t'
            ) + "\n"
        return error_message

    def get_last_sync(self):
        url = "https://{api_url}/1/user/{user_id}/devices.json".format(
            api_url=self.FitbitApi.API_URL,
            user_id=self._user_id,
        )
        response = self._request_data(url)
        data_idx = 0
        last_sync_str = response[data_idx][self.FitbitApi.LAST_SYNC_KEY]+"000"  # zeros pad microseconds for parsing
        str_format = "%Y-%m-%dT%H:%M:%S.%f"
        return datetime.datetime.strptime(last_sync_str, str_format)

    def get_steps(self, date: datetime.date = None):
        url = "https://{api_url}/1/user/{user_id}/{resource_path}/date/{date}/1d/{detail_level}.json".format(
            api_url=self.FitbitApi.API_URL,
            user_id=self._user_id,
            resource_path=self.FitbitApi.STEPS_RESOURCE_PATH,
            date=self._date_to_fitbit_date_string(date),
            detail_level=self.FitbitApi.STEPS_DETAIL_LEVEL_1_MIN,
        )
        response = self._request_data(url)
        return self._steps_response_to_dataframe(response)

    @staticmethod
    def _steps_response_to_dataframe(response):
        times = []
        steps = []
        for i in response['activities-steps-intraday']['dataset']:
            steps.append(i['value'])
            times.append(i['time'])
        return pandas.DataFrame({'Time': times, 'Steps': steps})

    def _request_data(self, url):
        headers = {"Authorization": "Bearer {}".format(self._access_token)}
        logging.info("GET request to '{}'".format(url))
        response = requests.get(
            url=url,
            headers=headers
        ).json()
        self._check_response_for_errors(response)
        return response

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
                    error_message = BackendFitbitClient._get_error_message_from_get_response(response)
                    logging.error(error_message, exc_info=True)
                    raise FitbitCredentialsError(error_message)

    @staticmethod
    def _date_to_fitbit_date_string(date: datetime.date = None):

        if date is None:
            return "today"

        return date.strftime('%Y-%m-%d')


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    client_id_ = "22BBNN"
    code_ = "fd4edb10e3c69581622fef73f2d1147ad8ebdb27"
    authorization_ = "MjJCQk5OOjUzMGRlYmI5YjA0OGVmODgwMTI3OWQxYmM2YzY5NzU1"
    fitbit_caller = BackendFitbitClient(
        client_id=client_id_,
        code=code_,
        authorization=authorization_,
        is_run_setup=True
    )
    print(fitbit_caller.get_steps())
    print(fitbit_caller.get_last_sync())
