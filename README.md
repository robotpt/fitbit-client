README
======

[![PyPI version](https://badge.fury.io/py/fitbit-client.svg)](https://badge.fury.io/py/fitbit-client)
[![Build Status](https://travis-ci.com/robotpt/fitbit-client.svg?branch=master)](https://travis-ci.com/robotpt/fitbit-client)
[![Coverage Status](https://coveralls.io/repos/github/robotpt/fitbit-client/badge.svg?branch=master)](https://coveralls.io/github/robotpt/fitbit-client?branch=master)

A Fitbit client that works from terminal to read steps data without launching a web browser or requiring that the user is signed in.

Features
--------
* No web sign-in is prompted when running the app
* Access doesn't expire
* Uses a one-time code to get the OAuth2 access token
* Saves a file with the credentials that it uses by default when run
* Exposes a function for generic requests to Fitbit's API
* Returns intraday steps data for a specified date in a Pandas Dataframe and the datetime of the last sync

Setup
-----

Follow the instructions [here](https://www.forkingbytes.com/blog/using-the-fitbit-api-from-a-command-line-application-in-go/) to obtain the following:
* Client ID
* Code
* Authorization

> Note that for access to intraday data, create a personal app.

Then, either
* Run this program and enter information when prompted
* Or pass this information as function arguments

You can then start making Fitbit API calls.  The program supports intraday steps and the last sync time with convenience functions, and there is also a function `get_url` for making generic requests to Fitbit's API.
