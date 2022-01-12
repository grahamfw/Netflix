#!/usr/local/bin/python3

# This script takes a Google Drive parent folder ID and credential file and tell you how many files and folders are contained within.

# Written by Graham Wells, graham.wells@gmail.com
# 1-11-2022

# Exerpted from the Google QuickStart repo: https://github.com/googleworkspace/python-samples/blob/master/drive/quickstart/quickstart.py

from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

# Specify your credential file here
credFile = '/path/to/file.json'

# Specify your Google Drive parent folder ID here
parentFolderId = ''

# Start with blank slate of creds

creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            credFile, SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())


def getNumberOfFilesFromParent(parentFolderId):
    # Run a query to get a list of all files in this source folder.
    try:
        listOfFiles = []
        service = build('drive', 'v3', credentials=creds)
        # Call the Drive v3 API
        results = service.files().list(q="mimeType != 'application/vnd.google-apps.folder' and parents in '{}'".format(parentFolderId),
                                       pageSize=9, fields="nextPageToken, files(id, name)").execute()
        # If there is more than one page, call the next page of results and add fiels to list
        for file in results['files']:
            listOfFiles.append(file)
        try:
            while results['nextPageToken']:
                results = service.files().list(q="mimeType != 'application/vnd.google-apps.folder' and parents in '{}'".format(parentFolderId),
                                               pageSize=9, pageToken=results['nextPageToken'], fields="nextPageToken, files(id, name)").execute()
                for file in results['files']:
                    listOfFiles.append(file)
        except KeyError:
            pass
        # items = listOfFiles.get('files', [])
        items = listOfFiles
        # if not items:
        #     print('No files found.')
        #     return
        count = len(items)
        return count
        # print('Files: ' + str(len(items)))
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


def getNumberOfFoldersFromParent(parentFolderId):
    # Run a query to get a list of all folders in this source folder
    try:
        listOfFiles = []
        service = build('drive', 'v3', credentials=creds)
        # Call the Drive v3 API
        results = service.files().list(q="mimeType = 'application/vnd.google-apps.folder' and parents in '{}'".format(
            parentFolderId), pageSize=9, fields="nextPageToken, files(id, name)").execute()
        # If there is more than one page, call the next page of results and add fiels to list
        for file in results['files']:
            listOfFiles.append(file)
        try:
            while results['nextPageToken']:
                results = service.files().list(q="mimeType = 'application/vnd.google-apps.folder' and parents in '{}'".format(parentFolderId),
                                               pageSize=9, pageToken=results['nextPageToken'], fields="nextPageToken, files(id, name)").execute()
                for file in results['files']:
                    listOfFiles.append(file)
        except KeyError:
            pass
        # items = listOfFiles.get('files', [])
        items = listOfFiles
        # if not items:
        #     print('No files found.')
        #     return
        count = len(items)
        return count
        # print('Folders: ' + str(len(items)))
        # for item in items:
        #     print(u'{0} ({1})'.format(item['name'], item['id']))
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


def main():
    fileCount = getNumberOfFilesFromParent(parentFolderId)
    folderCount = getNumberOfFoldersFromParent(parentFolderId)
    print('')
    print('Folders: ' + str(folderCount))
    print('Files: ' + str(fileCount))
    print('')


if __name__ == '__main__':
    main()
