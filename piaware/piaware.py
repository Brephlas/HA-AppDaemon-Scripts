import appdaemon.plugins.hass.hassapi as hass
from time import sleep
from datetime import datetime, time, timedelta
import requests
import h3

# Debug logs
DEBUG = False
DEBUG_EXIT_REASONS = False

# Home location (for distance calculation)
HOME = (43.3068, 0.7668)

# Configs
VOLUME_MODIFIER = 0.20 # increase by 20% of current volume 
HEIGHT_RELEVANT_AIRCRAFTS = 5700 # ignore flights that are higher than 5700 feet (to ignore aircrafts at traveling height)
DISTANCE_RELEVANT_AIRCRAFTS = 2000 # reduce volume if the aircraft is at a distance of 2000 feet
EXCEPTION_FLIGHTS = [''] # if there is one specific flight number circling above your location

# HA Media players
MEDIA_PLAYERS = ['media_player.x']
media_players_increment = {}
media_players_current_level = {}

class PiAware(hass.Hass):
    tracked_aicraft = []
    tracked_aicraft_steps = []
    volume_steps = 1

    def is_time_between(self, begin_time, end_time, check_time=datetime.now().time(), debug=False):
        # If check time is not given, default to current UTC time
        check_time = check_time or datetime.utcnow().time()
        check_time = check_time.replace(microsecond=0)
        
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else: # crosses midnight
            if debug:
                self.log(check_time)
            return check_time >= begin_time or check_time <= end_time

    def initialize(self):
        self.run_every(self.run, "now+10", 10)
        # self restart
        self.run_daily(self.restart_myself, "05:10:00")
        self.run_daily(self.restart_myself, "17:10:00")

def restart_myself(self, kwargs):
    # there were some issues in AppDaemon with the current time so restart the app regularly
    self.restart_app("PiAware")

def check_conditions_against_state(self, check_list):
    """
    Takes a media player and value to check the state against
    Example argument for check_list:
        (media_player.x, "playing")
    """
    for i in check_list:
        if self.get_state(i[0]) != i[1]:
    if DEBUG_EXIT_REASONS:
        self.log("exit due to " + str(i[0]) + " state being " + self.get_state(i[0]))
        return False
    
    return True

def check_conditions_against_attribute(self, check_list):
    """
    Takes a media player, attribute and value or list to check the attribute against
    Example arguments for check_list:
        (media_player.x, "is_volume_muted", False)
        (media_player.y", "source", ['DESKTOP-x'])
    """
    for i in check_list:
        if type(i[2]) == list:
            if not self.get_state(i[0], i[1]) in i[2]:
                if DEBUG_EXIT_REASONS:
                    self.log("exit due to " + str(i[0]) + " attribute " + str(i[1]) + " being " + str(self.get_state(i[0], i[1])) + " and not in list")
                    self.log(i[2])
                return False
    else:
        if not self.get_state(i[0], i[1]) == i[2]:
            if DEBUG_EXIT_REASONS:
                self.log("exit due to " + str(i[0]) + " attribute " + str(i[1]) + " being " + str(self.get_state(i[0], i[1])))
            return False
    return True

def check_not_run_conditions(self):
    # the nearby airport is not allowed to have starting planes during the night 
    if self.is_time_between(time(23,00), time(8,00)):
        if DEBUG_EXIT_REASONS:
            self.is_time_between(time(23,00), time(8,00), debug=True)
            self.log("Airport not operational")
    return 1

    # some check conditions which must be fulfilled to adjust volume level
    check_list = [
        ("input_boolean.disable_piaware_volume_adjustment", 'off'), #manual switch to be able to turn the automation off in home assistant
        ("device_tracker.piaware_device", "home"), # piaware device
        ("person.xy", "home")
    ]
    
    if self.check_conditions_against_state(check_list):
        # all conditions are fullfilled
        return True
    else:
        # one condition is not fullfilled, so abort
        return False

def check_not_run_conditions_media_players(self, media_player):
    # specific checks per media_player
    match media_player:
        case 'media_player.spotify_breph':
            # check if source matches PC or laptop
            check_list_attribute= [
                ("media_player.spotify_breph", "source", ['DESKTOP-x']) # check if spotify is playing on my desktop computer (i do not need volume adjustment if it is playing on e.g. the phone)
            ]
            
            if not self.check_conditions_against_attribute(check_list_attribute):
                # one condition is not fullfilled, so continue
                return False
        
            check_list = [
                ("binary_sensor.pc_running_game", "off"), # i have a sensor in case a game is running (since i have the headset on then i dont need volume adjustment)
                ("binary_sensor.window_sensor", "on") # only adjust if window is open
            ]
            
            if not self.check_conditions_against_state(check_list):
                # one condition is not fullfilled, so abort
                return False
    
        case 'media_player.desktop_pc':
            # check if game is running (and therefore not volume modification required)
            check_list = [
                ("binary_sensor.pc_running_game", "off"), # same as above as this is the same room
                ("binary_sensor.window_sensor", "on") 
            ]
            
            if not self.check_conditions_against_state(check_list):
                # one condition is not fullfilled, so return
                return False
    
        case 'media_player.lg':
            # check window sensor
            check_list = [
                ("binary_sensor.window_sensor_tv_room", "on")
            ]
            
            if not self.check_conditions_against_state(check_list):
                # one condition is not fullfilled, so continue
                return False
            # check if tv is muted
            check_list_attribute= [
                (media_player, "is_volume_muted", False)
            ]
            
            if not self.check_conditions_against_attribute(check_list_attribute):
                # one condition is not fullfilled, so continue
                return False
            
            # all conditions are fullfilled
            return True

def modify_volume(self, inc = True, big_machine = False):
    media_players_to_modify_volume = []
    
    for media_player in MEDIA_PLAYERS:
        state = self.get_state(media_player)
        if state in ['playing', 'on']:
            # check special conditions for different media players
            if not self.check_not_run_conditions_media_players(media_player):
                continue
            media_players_to_modify_volume.append(media_player)
    
    if DEBUG:
        self.log(media_players_current_level)
    
    for media_player in media_players_to_modify_volume:
    
    if inc:
        level = self.get_state(media_player, attribute='volume_level')
        increment_value = round(VOLUME_MODIFIER * level, 2)

        # cap maximum increment_value
        increment_value = 0.05 if increment_value > 0.05 else increment_value

        if big_machine:
            increment_value *= 2

        # create dict for increment_value per media_player
        media_players_increment[media_player] = round(increment_value, 2)
        media_players_current_level[media_player] = level
        level = round(media_players_current_level[media_player] + media_players_increment[media_player], 2)
    else:
    level = round(media_players_current_level[media_player], 2)


    if DEBUG:
        self.log("Change volume of "+str(media_player)+" to "+str(level))
    # actually increase the volume of the media player
    # uses the script from: https://github.com/MaxVRAM/HA-Fade-Volume-Script
    # you can also use the service call media_player.volume_up 
    self.call_service("script/turn_on", entity_id="script.media_player_fade_volume", variables={"target_player": media_player, "target_volume": level, "duration": 1, "curve": "linear"})
    # sleep to let the fade volume script execute
    sleep(1)

def run(self, kwargs):
    # stop if not required to run at all
    if not self.check_not_run_conditions():
        return

    r = requests.get('http://<ip-of-piaware>:8080/data/aircraft.json')
    json_airplanes = r.json()

for aircraft in json_airplanes['aircraft']:
    try:
        altitude = aircraft['alt_baro']
        flight = aircraft['flight'].strip()
        lat = aircraft['lat']
        lon = aircraft['lon']
        category = aircraft['category']
        big_machine = category == 'A5' # A5 means 4 turbine machine
        aircraft_gps = (lat, lon)
        # get distance in meters
        distance = int(h3.point_dist(HOME, aircraft_gps, unit='m'))

    # Exit in case of exceptions (e.g. helicopters for flightseeing)
    if flight in EXCEPTION_FLIGHTS:
        if DEBUG:
            self.log('Skip due to flight being in exceptions list: '+str(flight))
        continue
    
    # Exit in case of small aircrafts
    if category == 'A0':
        continue

    if not big_machine:
        if altitude < 3500:
            # increase the volume more if aircraft is closer than usual
            big_machine = True

    if flight not in self.tracked_aicraft:
        if int(altitude) < HEIGHT_RELEVANT_AIRCRAFTS and distance < DISTANCE_RELEVANT_AIRCRAFTS:
            if DEBUG:
                if big_machine:
                    self.log("Flight "+str(flight)+" ("+str(lat) + ", " + str(lon)+"). Height: "+str(altitude)+". Distance to aircraft: " + str(distance) + " - Big Machine")
                else:
                    self.log("Flight "+str(flight)+" ("+str(lat) + ", " + str(lon)+"). Height: "+str(altitude)+". Distance to aircraft: " + str(distance))
    
            self.tracked_aicraft.append(flight)
            self.tracked_aicraft_steps.append(self.volume_steps)
            # increase volume
            self.modify_volume(inc=True, big_machine=big_machine)
    else:
        if int(altitude) > HEIGHT_RELEVANT_AIRCRAFTS or distance > (DISTANCE_RELEVANT_AIRCRAFTS + 700):
            self.tracked_aicraft.remove(flight)
            self.volume_steps = self.tracked_aicraft_steps.pop(0)
            # decrease volume
            self.modify_volume(inc=0, big_machine=big_machine)
    except KeyError:
        pass