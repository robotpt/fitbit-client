from backend_fitbit_client import BackendFitbitClient
import logging

logging.basicConfig(level=logging.INFO)

fitbit_caller = BackendFitbitClient()
print(fitbit_caller.get_steps())
print(fitbit_caller.get_last_sync())
