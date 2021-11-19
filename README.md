# chromecast-dashboard

Ambient photos - with videos!

My kids love looking at recent photos on the Chromecast, but since a lot of them are actually videos, they wouldn't' show up.

So I made my own chromecast app that also displays videos as well!

Here's how it works:

1. (Optional) Create a new project at https://console.cloud.google.com/
    1. Enable the Google Photos API
    2. Create a new api key
2. Go to this repo's github pages/sender.html at https://eerovil.github.io/chromecast-dashboard/chromecast_dashboard/sender.html
3. Input your own api key + clientID (Or use my keys, the quota may or may not be over the limit)
4. Click "Sign in" and allow access to Google Photos for the app.
5. Connect to your chromecast using the big chromecast button.
6. Select albums to show in the ambient. If you check the "hidden" box, any media in that album will not be shown (useful for "All photos")
6. Click "Send".

The sender application will then send your api token to the chromecast. The Chromecast will fetch media and display two items for 10 seconds, then switch.

Every other switch the media on the right side will be a video. It will be looped for some time, or played fully if it's under 5 minutes.

# TODO

* Modifiable timeout per image shown
* Better handling of different aspect ratios
* Something happens after 1 hour and the images/videos start breaking
* Muting videos is not working (Some videos are muted, others are not. This is apparently a Chrome bug)
