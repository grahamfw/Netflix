#!/usr/local/bin/python3

## This script takes a Google Drive source parent folder ID, destination parent folder ID and credential file and will recursively copy
# files and folder structure between source and destination. 

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

# SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
SCOPES = ['https://www.googleapis.com/auth/drive']

# Download client secret json file from Google or formulate from a secrets manager.
credFile = '/path/to/file.json'

# Specify your source and destination folder IDs here
destinationFolderId = ''
sourceFolderId = ''

##### Do not edit below this line #####

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

# Function that gets the list of files (if any) for a given folder ID


def getFilesFromParent(parentFolderId):
    # Run a query to get a list of all files in this source folder.
    try:
        listOfFiles = []
        service = build('drive', 'v3', credentials=creds)
        # Call the Drive v3 API
        results = service.files().list(q="mimeType != 'application/vnd.google-apps.folder' and parents in '{}' and trashed != true".format(
            parentFolderId), pageSize=9, fields="nextPageToken, files(id, name)").execute()
        # If there is more than one page, call the next page of results and add files to list
        for file in results['files']:
            listOfFiles.append(file)
        try:
            while results['nextPageToken']:
                results = service.files().list(q="mimeType != 'application/vnd.google-apps.folder' and parents in '{}' and trashed != true".format(parentFolderId),
                                               pageSize=9, pageToken=results['nextPageToken'], fields="nextPageToken, files(id, name)").execute()
                for file in results['files']:
                    listOfFiles.append(file)
        except KeyError:
            pass
        return listOfFiles
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')

# Function that gets a list of nested folders (if any) for a given folder ID


def getFoldersFromParent(parentFolderId):
    # Run a query to get a list of all folders in this source folder
    try:
        listOfFolders = []
        service = build('drive', 'v3', credentials=creds)
        # Call the Drive v3 API
        results = service.files().list(q="mimeType = 'application/vnd.google-apps.folder' and parents in '{}' and trashed != true".format(
            parentFolderId), pageSize=9, fields="nextPageToken, files(id, name)").execute()
        # If there is more than one page, call the next page of results and add files to list
        for folder in results['files']:
            files = getFilesFromParent(parentFolderId)
            folder['files'] = files
            listOfFolders.append(folder)
        try:
            while results['nextPageToken']:
                results = service.files().list(q="mimeType = 'application/vnd.google-apps.folder' and parents in '{}' and trashed != true".format(parentFolderId),
                                               pageSize=9, pageToken=results['nextPageToken'], fields="nextPageToken, files(id, name)").execute()
                for folder in results['files']:
                    files = getFilesFromParent(parentFolderId)
                    folder['files'] = files
                    listOfFolders.append(folder)
        except KeyError:
            pass
        if len(listOfFolders) > 0:
            for folder in listOfFolders:
                nestedFolders = getFoldersFromParent(folder['id'])
                if len(nestedFolders) > 0:
                    folder['nestedFolders'] = nestedFolders
        return listOfFolders
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


# Function to create the actual folders, recursively, to replicate nesting.

def createFolders(listOfFolders, currentParent):
    for item in listOfFolders:
        file_metadata = {
            'name': item['name'],
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [currentParent]
        }
        service = build('drive', 'v3', credentials=creds)
        newFolder = service.files().create(body=file_metadata, fields='id').execute()
        try:
            if item['nestedFolders']:
                # print("Nested folders appears to be " + str(item['nestedFolders']))
                newParent = newFolder['id']
                createFolders(item['nestedFolders'], newParent)
            if len(item['files']) > 0:
                for actualFile in item['files']:
                    file_metadata = {
                        'name': actualFile['name'],
                        'parents': [newFolder['id']]
                    }
                    result = service.files().copy(
                        fileId=actualFile['id'], body=file_metadata).execute()
                    # print("Copied file with ID of " + actualFile['id'] + " and name of " + actualFile['name'])
        except KeyError:
            pass

            
# Main function to take the source and copy the folders to the destination


def main(sourceFolderId, destinationFolderId):
    # Parse the folders/files in the source directory
    listOfFolders = getFoldersFromParent(sourceFolderId)
    createFolders(listOfFolders, destinationFolderId)


if __name__ == '__main__':
    main(sourceFolderId, destinationFolderId)
