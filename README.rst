======
README
======

A Fitbit client that works from terminal (without launching a web browser to have the user is signed in).

********
Features
********

* No web sign-in is prompted when running the app
* Access token is renewed when it expires
* Saves a file with the credentials that it uses by default when run
* Exposes a function for generic requests to Fitbit's API

*****
Setup
*****

Follow the instructions [here](https://www.forkingbytes.com/blog/using-the-fitbit-api-from-a-command-line-application-in-go/) to obtain the following:
* Client ID
* Client Secret
* Code

> Note that for access to intraday data, create a personal app.

