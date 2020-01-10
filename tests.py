import unittest
from unittest import mock
from fitbit_client import FitbitClient, FitbitApiError, FitbitCredentialsError
import logging

logging.basicConfig(level=None)

class TestFitbitCaller(unittest.TestCase):

    @mock.patch('fitbit_client.yaml')
    @mock.patch('fitbit_client.requests')
    @mock.patch('fitbit_client.os.path.exists')
    @mock.patch('fitbit_client.input')
    def test_create_token_file_from_user_input(
            self, input_mock, exists_mock, requests_mock, yaml_mock
    ):

        foo_access_token = 'access'
        foo_scope = 'scope'
        foo_user_id = 'al'
        foo_token = {
            'access_token': foo_access_token,
            'scope': foo_scope,
            'user_id': foo_user_id
        }

        exists_mock.return_value = False
        response_mock = mock.Mock()
        response_mock.json.return_value = foo_token
        requests_mock.post.return_value = response_mock

        FitbitClient()

        assert input_mock.call_count == 3
        response_mock.json.assert_called()
        yaml_mock.dump.assert_called()

        saved_dict = yaml_mock.dump.call_args[0][0]
        assert saved_dict == foo_token

    @mock.patch('fitbit_client.yaml')
    @mock.patch('fitbit_client.requests')
    @mock.patch('fitbit_client.os.path.exists')
    @mock.patch('fitbit_client.input')
    def test_create_token_file_from_args(
            self, input_mock, exists_mock, requests_mock, yaml_mock
    ):

        foo_access_token = 'access'
        foo_scope = 'scope'
        foo_user_id = 'al'
        foo_token = {
            'access_token': foo_access_token,
            'scope': foo_scope,
            'user_id': foo_user_id
        }

        exists_mock.return_value = False
        response_mock = mock.Mock()
        response_mock.json.return_value = foo_token
        requests_mock.post.return_value = response_mock

        FitbitClient(client_id='foo', code='bar', authorization='baz')

        assert input_mock.call_count == 0
        response_mock.json.assert_called()
        yaml_mock.dump.assert_called()

        saved_dict = yaml_mock.dump.call_args[0][0]
        assert saved_dict == foo_token

    @mock.patch('fitbit_client.yaml')
    @mock.patch('fitbit_client.os.path.exists')
    @mock.patch('fitbit_client.input')
    def test_load_token_file(self, input_mock, exists_mock, yaml_mock):

        foo_access_token = 'access'
        foo_scope = 'scope'
        foo_user_id = 'al'
        foo_token = {
            'access_token': foo_access_token,
            'scope': foo_scope,
            'user_id': foo_user_id
        }

        exists_mock.return_value = True
        yaml_mock.load.return_value = foo_token

        FitbitClient()

        assert input_mock.call_count == 0
        yaml_mock.load.assert_called()

    @mock.patch('fitbit_client.yaml')
    @mock.patch('fitbit_client.os.path.exists')
    @mock.patch('fitbit_client.requests')
    @mock.patch('fitbit_client.input')
    def test_prompt_user_for_credentials_if_a_bad_token_is_stored(
            self, input_mock, requests_mock, exists_mock, yaml_mock
    ):

        foo_access_token = 'access'
        foo_scope = 'scope'
        foo_user_id = 'al'
        good_token = {
            'access_token': foo_access_token,
            'scope': foo_scope,
            'user_id': foo_user_id
        }
        bad_token = ['not a valid token']

        exists_mock.return_value = True
        yaml_mock.load.return_value = bad_token
        response_mock = mock.Mock()
        response_mock.json.return_value = good_token
        requests_mock.post.return_value = response_mock

        FitbitClient()

        assert input_mock.call_count == 3
        yaml_mock.load.assert_called()

        saved_dict = yaml_mock.dump.call_args[0][0]
        assert saved_dict == good_token

    @mock.patch('fitbit_client.yaml')
    @mock.patch('fitbit_client.requests')
    @mock.patch('fitbit_client.os.path.exists')
    @mock.patch('fitbit_client.input')
    def test_credentials_error(
            self, _, exists_mock, requests_mock, yaml_mock
    ):

        error_token = {
            'success': False,
            'errors': [
                {
                    'errorType': 'too good looking',
                    'message': 'are you free later?'
                },
                {
                    'errorType': 'extra medium',
                    'message': 'do you have something less medium'
                },
            ]
        }
        exists_mock.return_value = False
        response_mock = mock.Mock()
        response_mock.json.return_value = error_token
        requests_mock.post.return_value = response_mock

        self.assertRaises(
            FitbitCredentialsError,
            FitbitClient,
        )

        assert yaml_mock.dump.call_count == 0

    @mock.patch('fitbit_client.yaml')
    @mock.patch('fitbit_client.requests')
    @mock.patch('fitbit_client.os.path.exists')
    @mock.patch('fitbit_client.input')
    def test_bad_api_return(
            self, _, exists_mock, requests_mock, yaml_mock
    ):

        error_token = {
            'success': True,
        }
        exists_mock.return_value = False
        response_mock = mock.Mock()
        response_mock.json.return_value = error_token
        requests_mock.post.return_value = response_mock

        self.assertRaises(
            FitbitApiError,
            FitbitClient,
        )

        assert yaml_mock.dump.call_count == 0

    @mock.patch('fitbit_client.yaml')
    @mock.patch('fitbit_client.requests')
    @mock.patch('fitbit_client.os.path.exists')
    @mock.patch('fitbit_client.input')
    def test_connection_failure(
            self, _, exists_mock, requests_mock, yaml_mock
    ):
        error_token = {
            'crap reply': True,
        }
        exists_mock.return_value = False
        response_mock = mock.Mock()
        response_mock.json.return_value = error_token
        requests_mock.post.return_value = response_mock

        self.assertRaises(
            ConnectionError,
            FitbitClient,
        )

        assert yaml_mock.dump.call_count == 0
