from fitbit_client import FitbitClient
import logging
import datetime

logging.basicConfig(level=logging.INFO)

fitbit_caller = FitbitClient()
print(fitbit_caller.get_steps(
        datetime.date(2020, 1, 1)
))
print(fitbit_caller.get_last_sync())
