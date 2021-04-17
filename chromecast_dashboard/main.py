# coding: utf-8
import json
from flask import Flask, flash, request, redirect, send_from_directory
import random

import logging

from requests.models import Response

app = Flask(__name__)
app.secret_key = "super secret key"
app.logger.setLevel(logging.DEBUG)
with open('config.json', 'r') as config_file:
    app.config.update(json.load(config_file))
creds = None


@app.route('/', methods=['GET'])
def index():
    return send_from_directory('.', 'index.html')


@app.route('/iframe', methods=['GET'])
def index2():
    return send_from_directory('.', 'index_iframe.html')


@app.route('/get_image', methods=['GET'])
def get_image():
    return randomize_media(media_type="image")


@app.route('/get_video', methods=['GET'])
def get_video():
    return randomize_media(media_type="video")


@app.route('/log', methods=['POST'])
def log():
    app.logger.info("log: %s", request.get_json()['message'])
    return ''


@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response


def randomize_media(media_type="image"):
    """
    Get a random media id from all albums
    """
    albums = []
    try:
        with open('albums.json', 'r') as album_file:
            albums = json.load(album_file)
    except:
        app.logger.info("no albums")
        raise AttributeError()

    total_media_count = 0
    for album in albums:
        total_media_count += (len(album["cached_media_items"]) - 1)

    random_index = random.randint(0, total_media_count)

    # random_index = 77

    for album in albums:
        count = len(album["cached_media_items"])
        if random_index < count:
            ret = fetch_media_item(album, random_index)
            if ret['mimeType'].startswith(media_type):
                return ret
            else:
                return randomize_media(media_type=media_type)
        random_index -= count

    app.logger.error("Failed to get random image!")
    return None


def fetch_media_item(album, index=0):
    app.logger.info("Fetching index %s from album %s", index, album['title'])
    ret = None
    if len(album['cached_media_items']) > index:
        ret = album['cached_media_items'][index]
        app.logger.info("Found in cache!")
        app.logger.debug(ret['id'])
        return ret

    return ret


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5010")
