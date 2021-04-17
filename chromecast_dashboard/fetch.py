# coding: utf-8

# Fetches all albums from config. data is good for 1 hour!

import os
import json
import requests
import sys

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


dir_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dir_path, 'config.json'), 'r') as config_file:
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
        with open(os.path.join(dir_path, 'albums.json'), 'w') as f:
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
    if os.path.exists(os.path.join(dir_path, 'token.json')):
        creds = Credentials.from_authorized_user_file(os.path.join(dir_path, 'token.json'), SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(dir_path, 'credentials.json'), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(os.path.join(dir_path, 'token.json'), 'w') as token:
            token.write(creds.to_json())


def get_all_albums():
    global creds
    global albums
    headers = {'Authorization': 'Bearer {}'.format(creds.token)}
    albums_left = set(config['ALBUMS'].keys())
    pageToken = ""
    while albums_left:
        response = requests.get(
            'https://photoslibrary.googleapis.com/v1/albums?pageSize=50' + pageToken,
            headers=headers
        )
        for album_data in response.json()["albums"]:
            if album_data['title'] in config['ALBUMS']:
                print("Found album " + album_data['title'])
                album_data['cached_media_items'] = []
                album_data['config'] = config['ALBUMS'][album_data['title']]
                albums.append(album_data)
                albums_left.remove(album_data['title'])
        if not response.json().get("nextPageToken"):
            print("Last page, not found: " + albums_left)
            return
        pageToken = "&pageToken={}".format(response.json()["nextPageToken"])


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
    while index >= 0 and page_token is not None:
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
        page_token = data.get("nextPageToken", None)
        album['cached_page_token'] = page_token
        persist_cache()
        if index < 100 and index < len(data["mediaItems"]):
            ret = data["mediaItems"][index]
            break
        index -= 100

    if not ret:
        print("Not found item")
        return

    print("Found mediaitem! (cache size %s)", len(album['cached_media_items']))
    print("%s", ret['id'])
    return ret


if __name__ == '__main__':
    init_oauth()
    get_all_albums()
    for album in albums:
        if len(sys.argv) > 1:
            fetch_media_item(album, int(sys.argv[1]) - 1)
            continue
        fetch_media_item(album, int(album['mediaItemsCount']) - 1)
