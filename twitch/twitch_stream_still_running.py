import appdaemon.plugins.hass.hassapi as hass
import re
from urllib.request import Request, urlopen
import datetime
import json

DEBUG = False
CHANNEL_NAME = ''

class TwitchStreamStillRunning(hass.Hass):
    def initialize(self):
        self.listen_event(self.run, "twitch_streamstillrunning")

    def run(self, event, data, args):
        api_key = self.get_state("input_text.twitch_api_token")
        api_key = api_key.replace('\r', '').strip()
        header = {"Authorization": "Bearer "+str(api_key), "Client-Id":"X"}
        if DEBUG:
            self.log('.'+api_key+'.')

        ############################## Get time for first stream
        try:
            # get user IDs from twitch API
            request = Request('https://api.twitch.tv/helix/streams?user_login='+str(CHANNEL_NAME), headers=header)
            data = urlopen(request).read()

            # load json schedule data
            json_data = json.loads(data.decode('utf-8'))
            # check if stream if running
            stream_running = True if len(json_data['data']) != 0 else False
            # set input_boolean accordingly
            if not stream_running:
                stream_over = self.get_entity("input_boolean.twitch_stream_over")
                stream_over.set_state(state="on")
            else:
                stream_over = self.get_entity("input_boolean.twitch_stream_over")
                stream_over.set_state(state="off")
        except:
            pass