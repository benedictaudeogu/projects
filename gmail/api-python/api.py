#!/usr/bin/python3
# -*- coding: latin-1 -*-
import os
import yaml
import pickle
import datetime
import requests
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
access = ['https://mail.google.com/']
# start_date = datetime.date(2023, 9, 17)

def authenticate():
    creds = None
    # restore token.pickle file every 7 days, starting on the date this feature was added
    # if(datetime.date.today() - start_date).days % 7 == 0 and os.path.exists("token.pickle"): 
    #     os.remove("token.pickle")

    # token.pickle stores the user's access and refresh tokens, created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no valid credentials availablle, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('../../credentials.json', access)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

service = authenticate()

# try catch block to handle authentication errors
try:
    service = authenticate()
except Exception as e:
    # print("!!!!!!!Error: %s." % e)
    
    # send push notification to user
    # Bot token and chat id are stored in secret.yaml (not commited)
    TOKEN = yaml.safe_load(open('../secret.yaml'))['TOKEN'] 
    CHAT_ID = yaml.safe_load(open('../secret.yaml'))['CHAT_ID']
    # print(TOKEN)
    message = "Gmail Authentication Error: %s. Authentication failed." % e
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"

    # Send the message
    print(requests.get(url).json())

# gather all email messages
def find(service, query):
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = []
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages

# number of promotional emails
# print(len(find(service, 'in:promotions')))

# delete promotional emails
def delete(service, query):
    messages_to_delete = find(service, query)
    if not messages_to_delete:
        print("No messages found.")
        return
    # to delete a single message with the delete API: service.users().messages().delete(userId='me', id=msg['id'])
    return service.users().messages().batchDelete(
      userId='me',
      body={
          'ids': [ msg['id'] for msg in messages_to_delete]
      }
    ).execute()

delete(service, 'in:promotions')
