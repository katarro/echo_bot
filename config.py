#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "") #ac16ec2d-980d-41e7-8eaa-f5898fc91247
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")#2lg8Q~MU1GUy7TlUqYQg1ZTSMWiOsr0e1dyBIaMp
