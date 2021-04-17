# coding: utf-8

# Fetches all albums from config. data is good for 1 hour!

import os
import json
import requests
import sys

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


with open('config.json', 'r') as config_file:
    config = json.load(config_file)
creds = None
albums = []
persist_lock = False


def persist_cache():
    global persist_lock
    if persist_lock:
        return
    persist_lock = True
    try:
        with open('albums.json', 'w') as f:
            json.dump(albums, f)
    except Exception as e:
        print(e)

    persist_lock = False


def init_oauth():
    SCOPES = [
        "https://www.googleapis.com/auth/photoslibrary.readonly",
        "https://www.googleapis.com/auth/photoslibrary.sharing"
    ]
    global creds
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())


def get_all_albums():
    global creds
    headers = {'Authorization': 'Bearer {}'.format(creds.token)}
    response = requests.get(
        'https://photoslibrary.googleapis.com/v1/albums',
        headers=headers
    )
    for album_data in response.json()["albums"]:
        if album_data['title'] in config['ALBUMS']:
            album_data['cached_media_items'] = []
            album_data['config'] = config['ALBUMS'][album_data['title']]
            albums.append(album_data)


def fetch_media_item(album, index=0):
    print("Fetching index %s from album %s", index, album['title'])
    global creds
    headers = {'Authorization': 'Bearer {}'.format(creds.token)}
    page_token = ""
    counter = 0
    ret = None
    if len(album['cached_media_items']) > index:
        ret = album['cached_media_items'][index]
        print("Found in cache!")
        print(ret['id'])
        return ret
    elif len(album['cached_media_items']) > 0 and album.get('cached_page_token', None):
        print("Cache exists, but not long enough.")
        page_token = album['cached_page_token']
        counter += len(album['cached_media_items'])
        index -= counter
    while index >= 0:
        print("Fetching page.. (items %s to %s)", counter, counter + 100)
        response = requests.post(
            'https://photoslibrary.googleapis.com/v1/mediaItems:search',
            headers=headers,
            data={
                "albumId": album["id"],
                "pageSize": "100",
                "pageToken": page_token,
            }
        )
        data = response.json()
        if "mediaItems" not in data:
            print(json.dumps(data, indent=4))
            return Response("error (quota?)", status=500)
        counter += 100
        if len(album['cached_media_items']) < counter:
            album['cached_media_items'] += data["mediaItems"]
        page_token = data["nextPageToken"]
        album['cached_page_token'] = page_token
        persist_cache()
        if index < 100:
            ret = data["mediaItems"][index]
            break
        index -= 100

    print("Found mediaitem! (cache size %s)", len(album['cached_media_items']))
    print("%s", ret['id'])
    return ret


if __name__ == '__main__':
    init_oauth()
    get_all_albums()
    for album in albums:
        if len(sys.argv) > 1:
            fetch_media_item(album, int(sys.argv[1]) - 1)
            break
        fetch_media_item(album, int(album['mediaItemsCount']) - 1)
