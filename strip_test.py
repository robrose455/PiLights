import board
import neopixel
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser


config = configparser.ConfigParser()
config.read('config.cfg')

LED_COUNT = 30  # Number of LED pixels.
LED_PIN = board.D18  # GPIO pinW

client_id = config.get('SPOTIFY', 'CLIENT_ID')
client_secret = config.get('SPOTIFY', 'CLIENT_SECRET')

scope = "user-read-currently-playing", "user-read-playback-state", "user-modify-playback-state"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(scope=scope,
                              redirect_uri="http://127.0.0.1:5000/login/authorized",
                              client_id=client_id,
                              client_secret=client_secret,
                              open_browser=False
                              )
)
print("test")
strip = neopixel.NeoPixel(
    LED_PIN, LED_COUNT
)
def get_current_track_id():
    
    print("test pre")
    response = sp.current_user_playing_track()
    print("test post")
    print(response)
    track_id = response['item']['id']

    return track_id


def get_rhythm(track_id):
    response = sp.audio_analysis(track_id)
    audio_analysis = response['beats']
    beats = []
    for i in range(len(audio_analysis)):
        beats.append(audio_analysis[i]['start'])

    return beats


def get_playback_position():
    response = sp.current_playback()
    playback_pos_ms = response["progress_ms"]

    return playback_pos_ms


def play_song(beats, playback):
    
    sp.pause_playback()
    sp.start_playback(context_uri='spotify:playlist:6mf5APVavd17vvPWzxRaq8', offset={
                      "position": 5}, position_ms=0)

    for i in range(len(beats)):

        print(beats[i])
        strip.fill((255, 0, 0))
        strip.show()

        wait_time = 0
        if i != len(beats):
            wait_time = beats[i + 1] - beats[i]
        strip.fill((0, 0, 0))
        strip.show()

        time.sleep(wait_time)


if __name__ == '__main__':

    play_song(beats=get_rhythm(track_id=get_current_track_id()), playback=get_playback_position())
