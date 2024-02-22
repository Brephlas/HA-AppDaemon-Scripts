import appdaemon.plugins.hass.hassapi as hass
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

CLIENT_ID = 'x'
CLIENT_SECRET = 'x'
WAVELENGTH_SONGS = ['x'] # wavelength effect for some specific songs only (list of song ID's)

DEBUG = True

class SpotifyLedFXUpdateScene(hass.Hass):
    def initialize(self):
        self.listen_event(self.default, "spotify_ledfx_update_scene")

    def run(self, event, data, args):
        client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)
        
        media_player_spotify = self.get_entity('media_player.spotify_x')
        media_content_id = media_player_spotify.get_state(attribute="media_content_id")

        if media_content_id:
            song_id = media_content_id.split(':')[-1]

            # Songs that work best with wavelength
            if song_id in WAVELENGTH_SONGS:
                self.call_service("rest_command/ledfx_scene_by_id", name = "default_wavelength")
                return

            features = sp.audio_features(song_id)
            
            if DEBUG:
                self.log(features)

            tempo = features[0]['tempo']
            danceability = features[0]['danceability']*100

            # set scenes based on tempo
            if int(tempo) > 130:
                self.call_service("rest_command/ledfx_scene_by_id", name = "party")
            elif int(tempo) > 100:
                self.call_service("rest_command/ledfx_scene_by_id", name = "partyslower")
            elif int(tempo) > 70:
                self.call_service("rest_command/ledfx_scene_by_id", name = "partyslow")
            else:
                self.call_service("rest_command/ledfx_scene_by_id", name = "wavelength_mirror")
