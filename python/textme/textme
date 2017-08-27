#!/bin/python
import sys
from keys import account_sid, auth_token
from twilio.rest import Client

body = sys.argv[1]
client = Client(account_sid, auth_token)

message = client.api.account.messages.create(to="+16095007081",
                                             from_="+12316749266",
                                             body=body)
