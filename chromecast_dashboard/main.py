# coding: utf-8
import os
import json
from flask import Flask, flash, request, redirect, send_from_directory
import requests
import random

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import logging

app = Flask(__name__)
app.secret_key = "super secret key"
app.logger.setLevel(logging.INFO)
with open('config.json', 'r') as config_file:
    app.config.update(json.load(config_file))
creds = None
albums = []


@app.route('/', methods=['GET'])
def index():
    return send_from_directory('.', 'index.html')


@app.route('/iframe', methods=['GET'])
def index2():
    return send_from_directory('.', 'index_iframe.html')


@app.route('/get_image', methods=['GET'])
def get_image():
    return randomize_image()


@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response


def randomize_image():
    """
    Get a random media id from all albums
    """
    total_media_count = 0
    for album in albums:
        total_media_count += int(album["mediaItemsCount"]) - 1
    
    # total_media_count = 200
    if len(albums[0]['cached_media_items']) == 0:
        total_media_count = 100
    
    random_index = random.randint(0, total_media_count)

    # random_index = 77

    for album in albums:
        count = int(album["mediaItemsCount"])
        if random_index < count:
            ret = fetch_media_item(album, random_index)
            return ret
            # if ret['mimeType'].startswith('video'):
            #     return ret
            # else:
            #     return randomize_image()
        random_index -= count

    app.logger.error("Failed to get random image!")
    return None

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
        if album_data['title'] in app.config['ALBUMS']:
            album_data['cached_media_items'] = []
            album_data['config'] = app.config['ALBUMS'][album_data['title']]
            albums.append(album_data)


def fetch_media_item(album, index=0):
    app.logger.info("Fetching index %s from album %s", index, album['title'])
    global creds
    headers = {'Authorization': 'Bearer {}'.format(creds.token)}
    page_token = ""
    counter = 0
    ret = None
    if len(album['cached_media_items']) > index:
        ret = album['cached_media_items'][index]
        app.logger.info("Found in cache!")
        app.logger.debug("%s", json.dumps(ret, indent=4))
        return ret
    elif len(album['cached_media_items']) > 0 and album.get('cached_page_token', None):
        app.logger.info("Cache exists, but not long enough.")
        page_token = album['cached_page_token']
        counter += len(album['cached_media_items'])
        index -= counter
    while index >= 0:
        app.logger.info("Fetching page.. (items %s to %s)", counter, counter + 100)
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
        counter += 100
        if len(album['cached_media_items']) < counter:
            album['cached_media_items'] += data["mediaItems"]
        if index < 100:
            ret = data["mediaItems"][index]
            break
        page_token = data["nextPageToken"]
        album['cached_page_token'] = page_token
        index -= 100

    app.logger.info("Found mediaitem! (cache size %s)", len(album['cached_media_items']))
    app.logger.debug("%s", json.dumps(ret, indent=4))
    return ret


if __name__ == '__main__':
    init_oauth()
    get_all_albums()
    app.run(host="0.0.0.0", port="5010")
