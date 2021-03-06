import board
import neopixel
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser
import random


config = configparser.ConfigParser()
config.read('config.cfg')

LED_COUNT = 80  # Number of LED pixels.
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

cool_colors = [ (43, 15, 153),
                (52, 0, 255),
                (0, 234, 255),
                (110, 234, 245),
                (192, 92, 255),
                (120, 0, 196),
                (156, 0, 255),
                (198, 129, 219),
                (96, 247, 222),
                (31, 156, 135),
                (0, 255, 212),
                (0, 122, 88),
                (219, 0, 208) ]


color_dic = {

    "Red": (255, 0, 0),
    "Orange": (255, 98, 0),
    "Yellow": (255, 255, 0),
    "Green": (0, 255, 26),
    "Light Blue": (0, 255, 208),
    "Blue": (0, 101, 252),
    "Purple": (165, 97, 201),
    "Pink": (245, 0, 233),

}


strip = neopixel.NeoPixel(
    LED_PIN, LED_COUNT, brightness=1.0, auto_write=True
)

def get_current_track_id():

    global current_song_id

    response = sp.current_user_playing_track()
    track_id = response['item']['id']
    current_song_id = track_id

    return track_id


def get_song_data(track_id):

    beats = []
    confidence = []
    levels = {}

    response = sp.audio_analysis(track_id)
    audio_analysis = response['tatums']

    response = sp.audio_features(track_id)

    levels['dance'] = response[0]['danceability']
    levels['energy'] = response[0]['energy']
    levels['valence'] = response[0]['valence']

    for i in range(len(audio_analysis)):
        beats.append(audio_analysis[i]['start'])
        confidence.append(audio_analysis[i]['confidence'])

    return beats, confidence, levels


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



            initial_buffer = beats[i + 1] - playback - 0.07
            initial_beat = i + 1

            if initial_buffer < 0.5:

                initial_buffer = beats[i + 2] - playback - 0.07
                initial_beat = i + 2

    print("Buffer: " + str(initial_buffer))
    print("Starting Beat: " + str(initial_beat))
    return initial_buffer, initial_beat, total_beats, beats

def control_lights(initial_buffer, initial_beat, total_beats, beats, confidence, levels):


    time.sleep(initial_buffer)
    cur_beat = initial_beat
    cur_color = (0,0,0)
    prev_color = (0,0,0)
    same_song = True
    is_playing = True
    steps = 1

    while cur_beat < total_beats - 2 and same_song is True and is_playing is True:

        #Beggining of operation buffer
        t1 = time.thread_time_ns()

        # Check if songs have changed
        response = sp.current_user_playing_track()
        track_id = response['item']['id']
        is_playing = response['is_playing']

        if track_id != current_song_id:
            same_song = False

        cur_beat += 1
        # 111, 255, 0
        p_r = prev_color[0]
        p_g = prev_color[1]
        p_b = prev_color[2]

        # 82, 189, 0
        c_r = cur_color[0]
        c_g = cur_color[1]
        c_b = cur_color[2]

        # -29, -66
        t_r = c_r - p_r
        t_g = c_g - p_g
        t_b = c_b - p_b

        # -0.29, -0.66
        tri = t_r / steps
        tgi = t_g / steps
        tbi = t_b / steps

        r = p_r
        g = p_g
        b = p_b

        for i in range(steps):

            r += tri
            g += tgi
            b += tbi

            strip.fill((int(r), int(g), int(b)))
            color = random.choice(list(color_dic.values()))
            for i in range(30):
                if i % 2 == 0:
                    strip[i] = color

        strip.brightness = confidence[cur_beat]
        strip.show()

        prev_color = cur_color
        cur_color = random.choice(list(color_dic.values()))


        # End of operation buffer
        t2 = time.thread_time_ns()
        t3 = (t2 - t1) / 1000000000
        t3 = 0

        fuck_it_buffer = 0.09
        wait_time = beats[cur_beat + 1] - beats[cur_beat] - fuck_it_buffer - t3

        print(wait_time)
        print(random.randint(0,9))

        time.sleep(wait_time)

    while is_playing is False:

        response = sp.current_user_playing_track()
        is_playing = response['is_playing']

    print("Song Ended")
    time.sleep(1)

if __name__ == '__main__':


    while True:

        beats, confidence, levels = get_song_data(track_id=get_current_track_id())
        initial_buffer, initial_beat, total_beats, beats = sync_to_song(beats, playback=get_playback_position())
        control_lights(initial_buffer, initial_beat, total_beats, beats, confidence, levels)
