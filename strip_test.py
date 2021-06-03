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

current_song_id = None

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(scope=scope,
                              redirect_uri="http://127.0.0.1:5000/login/authorized",
                              client_id=client_id,
                              client_secret=client_secret,
                              open_browser=False
                              )
)

colors = [ (255, 0, 0), (0, 0, 255) ]


strip = neopixel.NeoPixel(
    LED_PIN, LED_COUNT, brightness=1.0, auto_write=True
)

def get_current_track_id():

    global current_song_id

    response = sp.current_user_playing_track()
    track_id = response['item']['id']
    current_song_id = track_id

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

    return playback_pos_ms / 1000


def sync_to_song(beats, playback):

    #beats [2300,2306,2310...]
    #playback [2304]

    print("Playback: " + str(playback))
    initial_buffer = 0
    initial_beat = 0
    total_beats = len(beats)

    for i in range(len(beats)-1):

        # i = 2300
        if beats[i] < playback < beats[i + 1]:

            # playback is in between these beats

            # beats[i + 1] - 100ms delay
            #START LIGHTS
            # wait_time = beats[j] - beats[j + 1]

            initial_buffer = beats[i + 1] - playback - 0.07
            initial_beat = i + 1

            if initial_buffer < 0.5:

                initial_buffer = beats[i + 2] - playback - 0.07
                initial_beat = i + 2

    print("Buffer: " + str(initial_buffer))
    print("Starting Beat: " + str(initial_beat))
    return initial_buffer, initial_beat, total_beats, beats

def control_lights(initial_buffer, initial_beat, total_beats, beats):

    pulse_mode = False

    time.sleep(initial_buffer)

    cur_beat = initial_beat

    cur_color = 0

    brightness = 1.0

    same_song = True


    while cur_beat < total_beats - 2 and same_song is True:

        #Beggining of operation buffer
        t1 = time.thread_time_ns()

        # Check if songs have changed
        #response = sp.current_user_playing_track()
        #track_id = response['item']['id']

        #if track_id != current_song_id:
            #same_song = False

        cur_beat += 1

        strip.fill(colors[cur_color])


        cur_color += 1
        if cur_color == len(colors):
            cur_color = 0

        # End of operation buffer
        t2 = time.thread_time_ns()
        t3 = (t2 - t1) / 10000000

        if not pulse_mode:
            t3 = 0

        print("Time Elapsed: " + str(t3))

        wait_time = beats[cur_beat + 1] - beats[cur_beat] - (t3/100)

        print(wait_time)

        time.sleep(wait_time)

    print("Song Ended")
    time.sleep(2)

def testing():

    color = None

    for i in range(10):

        if i % 2 == 0:

            color = (255, 0, 0)

        else:

            color = (0, 0, 255)


        strip[i] = color





if __name__ == '__main__':


    while True:
        initial_buffer, initial_beat, total_beats, beats = sync_to_song(beats=get_rhythm(track_id=get_current_track_id()), playback=get_playback_position())
        control_lights(initial_buffer, initial_beat, total_beats, beats)
