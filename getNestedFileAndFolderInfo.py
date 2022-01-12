#!/usr/local/bin/python3

# This script takes a Google Drive parent folder ID and credential file and will generate a report of how many nested folders are contained
# within as well as how many nested files.

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

# Download client secret json file from Google or formulate from a secrets manager.
credFile = '/path/to/file.json'

# Specify the parent folder ID that you want to get data about
parentFolderId = ''

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

# Function that recursively grabs folder and file counts for a given source folder.


def getFolderAndFileCount(object, folderCountTotal, fileCountTotal):
    try:
        if object['nestedFolders']:
            # Has nested folders. Call function again on nested object
            for folder in object['nestedFolders']:
                folderCountTotal = folderCountTotal + 1
                # print("Checking in folder with ID of " + folder['id'])
                folderCountTotal, fileCountTotal = getFolderAndFileCount(
                    folder, folderCountTotal, fileCountTotal)
    except KeyError:
        pass
        # folderCountTotal = folderCount
    if len(object['files']) > 0:
        fileCountTotal = fileCountTotal + len(object['files'])
    # else:
    #     fileCountTotal = fileCount
    return folderCountTotal, fileCountTotal


# Create a list of objects where each object contains folder ID, folder name, list of files (if any), and a nested folders object (if any)
# The nested folders may contain other nested folder objects and have the same format.

allFoldersAndFiles = getFoldersFromParent(parentFolderId)


def main(allFoldersAndFiles):
    # Given a list of objects, recursively count the number of folders and files under the top level of folders.
    # Create a new list of objects that we can reference later (containing folder ID, nested folder count, and nested file count)
    allFolderAndFileInfo = []
    for parentFolderObj in allFoldersAndFiles:
        folderAndFileCountByParentFolderId = {}
        folderCount, fileCount = getFolderAndFileCount(parentFolderObj, 0, 0)
        folderAndFileCountByParentFolderId['id'] = parentFolderObj['id']
        folderAndFileCountByParentFolderId['name'] = parentFolderObj['name']
        folderAndFileCountByParentFolderId['folderCount'] = folderCount
        folderAndFileCountByParentFolderId['fileCount'] = fileCount
        allFolderAndFileInfo.append(folderAndFileCountByParentFolderId)

    # Print all folder and file info
    for parentFolder in allFolderAndFileInfo:
        print("")
        print("Folder ID: " + parentFolder['id'])
        print("Folder Name: " + parentFolder['name'])
        print("Nested Folder Count: " + str(parentFolder['folderCount']))
        print("Nested File Count: " + str(parentFolder['fileCount']))

    # Get all nested folders counts. Total includes the top level folders under the source folder ID, and print it.
    parentFoldersCount = len(allFolderAndFileInfo)
    nestedFolderCount = parentFoldersCount
    for parentFolder in allFolderAndFileInfo:
        nestedFolderCount = nestedFolderCount + parentFolder['folderCount']

    print("")
    print("Total Nested Folders: " + str(nestedFolderCount))
    print("")


if __name__ == '__main__':
    main(allFoldersAndFiles)
