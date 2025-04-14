#!/usr/bin/env python3
__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2024 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.1.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

# Run this class from the root dir as:
# PYTHONPATH=.:BingoBot/lib/python3.12/site-packages python util/CreateNewAuthToken.py

import google_auth_oauthlib.flow
import os
import sys

from config.ClassLogger import ClassLogger, LogLevel
from config.Config import Config
from config.Globals import GLOBALVARS

__LOGGER__ = ClassLogger(__file__)

def main():
    __LOGGER__.log(LogLevel.LEVEL_INFO, "Attempting to create a new youtube token.")

    SCOPES = ["https://www.googleapis.com/auth/youtube"]

    # Init the google auth flow
    configNameSecrets = "YTCredFile"
    configNameToken = "YTTokenFile"
    client_secrets_file = f"{GLOBALVARS.PROJ_ROOT}/{Config().getConfig(configNameSecrets)}"
    tokenFile = f"{GLOBALVARS.PROJ_ROOT}/{Config().getConfig(configNameToken)}"

    # Verify the file configurations are set
    if not client_secrets_file:
        __LOGGER__.log(LogLevel.LEVEL_CRIT, f"There is no \"{configNameSecrets}\" configured, please add it to the configuration ({GLOBALVARS.FILE_CONFIG_GENERAL})")
        sys.exit(1)
    if not tokenFile:
        __LOGGER__.log(LogLevel.LEVEL_CRIT, f"There is no \"{configNameToken}\" configured, please add it to the configuration ({GLOBALVARS.FILE_CONFIG_GENERAL})")
        sys.exit(1)

    __LOGGER__.log(LogLevel.LEVEL_INFO, f"Attemping to create oauth token using the secret file: {client_secrets_file}")
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)

    # Spawn browser login
    print("Generating new auth token, please follow the instructions in the browser")
    oauthCred = flow.run_local_server()

    # Write oauth token to file
    logstr = f"New auth token created, saving token to '{tokenFile}'"
    print(logstr)
    __LOGGER__.log(LogLevel.LEVEL_INFO, logstr)
    fp = os.open(tokenFile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fp, "w") as file:
        file.write(oauthCred.to_json())
        file.close()

if __name__ == '__main__':
    main()

