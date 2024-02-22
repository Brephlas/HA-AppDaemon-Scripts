import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, time
import rpyc

DEBUG = False

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time

class WledInfo(hass.Hass):
    rpyc_misc = None

    def initialize(self):
        # debug trigger
        if DEBUG:
            self.log("enabled debug trigger")
            self.listen_state(self.run, "input_button.wled_info_debug_trigger") # debug trigger
        # turn on triggers
        self.listen_state(self.run, "binary_sensor.aqara_motion_corridor_occupancy_occupancy", new="on")
        self.listen_state(self.run, "binary_sensor.aqara_door_switch_wohnungstur_contact", new="on")
        self.listen_state(self.run_if_home, "sensor.kuche_timers", new="unavailable", duration = 5) # timers after 5 seconds
        self.listen_event(self.run_if_home, "wled_info_turn_on")
        # update triggers
        self.listen_state(self.update, "input_boolean.tonne_reminder", new="on")
        self.listen_event(self.update, "wled_info_update")
        # turn off triggers
        self.listen_state(self.turn_off, "binary_sensor.aqara_motion_corridor_occupancy_occupancy", new = "off", duration = 60) # 1 minute
        self.listen_state(self.turn_off, "binary_sensor.aqara_door_switch_wohnungstur_contact", new="off", duration = 300) # 5 minutes
        self.listen_state(self.turn_off, "binary_sensor.aqara_door_switch_doorbell_contact", old="on", new="off") # doorbell
        self.listen_state(self.turn_off, "sensor.kuche_timers", old="unavailable") # timers
        self.listen_state(self.turn_off, "switch.schreibtischlampe_2", old="off", new="on") # WLED ceiling
        self.listen_event(self.turn_off, "homeassistant.shutdown")
        self.listen_event(self.turn_off, "wled_info_turn_off")
        # regular self restart
        self.run_daily(self.restart_myself, "03:03:00")

    def debug_trigger(self, entity, attribute, old, new, kwargs):
        self.turn_off(entity, attribute, old, new, kwargs)
        self.run(entity, attribute, old, new, kwargs)

    def run_if_home(self, entity, attribute, old, new, kwargs):
        if self.get_state("person.personX") == 'home':
            if DEBUG:
                self.log("run_if_home triggered and turned on led")
            self.run(entity, attribute, old, new, kwargs)

    def update(self, entity, attribute, old, new, kwargs):
        if self.get_state("binary_sensor.aqara_motion_corridor_occupancy_occupancy") == 'on':
            self.run(entity, attribute, old, new, kwargs)
        else:
            self.rpyc_close()

    def restart_myself(self, kwargs):
        self.restart_app("WledInfo")

    def turn_off(self, entity, attribute, old, new, kwargs):
        # turn off
        if DEBUG:
            self.log("Turn led_info off")
        self.rpyc_close()

    def backlight(self, hex_value=0, mode=0):
        # do not display temperature led's between 23-23:59
        if is_time_between(time(23,00), time(23,59), datetime.now().time()):
            mode = 1
        
        # check if mode was set to not display any temperature led's
        if mode != 1:
            # get current temperature and set led_no accordingly
            current_outside_temperature = float(self.get_state("sensor.openweathermap_feels_like_temperature"))
            if int(current_outside_temperature) > 0:
                # current temperature *2 + threshold because the first 10 leds are ambient light
                led_no = int(current_outside_temperature * 2) + 20
            else:
                led_no = 20 - int(current_outside_temperature) # to get some kind of lower values

            # set forecast_led
            try:
                forecast_temperature = float(self.get_state("sensor.appdaemon_highest_temperature_today"))
            except ValueError:
                forecast_temperature = current_outside_temperature
            # check if positive or negative degrees
            if int(forecast_temperature) > 0:
                # forecast temperature *2 + threshold because the first 10 leds are ambient light
                forecast_led = int(forecast_temperature * 2) + 20
            else:
                forecast_led = 20 - int(forecast_temperature) # to get some kind of lower values

            if DEBUG:
                self.log("Turn on nightlight with led_no: "+str(led_no)+" ("+str(current_outside_temperature)+" \
                degrees Celsius) and forecast_led: "+str(forecast_led)+ " ("+str(forecast_temperature)+" degrees Celsius)")
                if hex_value != 0:
                    self.log("Hex: " + str(hex_value))

            # is biomuell active? Turn on extra led as notification
            biomuell = True if self.get_state("binary_sensor.biomuell") == 'on' else False
            if DEBUG:
                self.log("Biomuell Reminder is: "+str(biomuell))

            # inside temeperature
            temperature_inside = int(float(self.get_state("sensor.aqara_temp1_temperature")) * 2) + 20
            if DEBUG:
                self.log("Inside temperature is "+str(self.get_state("sensor.aqara_temp1_temperature")))

        self.rpyc_misc = rpyc.connect("<IP-Address-of-rpyc-server-host>", 18861)
        if mode != 1:
            self.rpyc_misc.root.nightlight(temperature_led=led_no, forecast_led=forecast_led, temperature_inside=temperature_inside, trash_hex=hex_value, biomuell=biomuell)
        elif mode == 1:
            self.rpyc_misc.root.nightlight(temperature_led=0, forecast_led=0, temperature_inside=0, trash_hex=0, biomuell=False)
        else:
            self.rpyc_misc.root.nightlight(temperature_led=led_no, forecast_led=forecast_led, temperature_inside=temperature_inside, trash_hex=hex_value, biomuell=biomuell)

    def run(self, entity, attribute, old, new, kwargs):
        # stop before setting new effect
        try:
            self.rpyc_close()
        except EOFError:
            pass

        # also do not set the light if it signals doorbell
        try:
            effect = self.get_state("light.wled_info")
            if DEBUG:
                self.log("WLED (Info) Effect: "+effect)
            if effect in ['unavailable', 'unknown', 'Heartbeat', 'Percent']:
                if DEBUG:
                    self.log("Exit due to WLED effect")
                return
        except:
            pass

        # abort if kitchen timer is running
        if self.get_state("sensor.kuche_timers") != 'unavailable':
            if DEBUG:
                self.log("Exit due to kuche timer running")
            return
        
        # check if the bed was occupied right before passing the corridor using history sensor
        history_bed_occupied = int(float(self.get_state("sensor.history_stats_bett_belegt_kurz")) * 60)
        if DEBUG:
            self.log("Bed " + str(history_bed_occupied) + " minutes occupied")

        if history_bed_occupied > 0 and not is_time_between(time(6,00), time(12,00), datetime.now().time()):
            # my phone is in flight mode during night so I am displayed as not_home
            # and I dont want temperature lights during the night when going to the bathroom during night
            if self.get_state("person.personX") != "home":
                if DEBUG:
                    self.log("Turn on lower light only")
                # if personX is not home light the stripe
                self.backlight(mode=1)
                return

        try:
            # check for trash state
            tonnen_state = self.get_state("sensor.tonnenbutton")
            tonnen_state_list = tonnen_state.split("|")
            if int(tonnen_state_list[1]) == 1 and self.get_state("input_boolean.tonne_reminder") == 'off' and is_time_between(time(16,00), time(0,00), datetime.now().time()):
                trash_type = tonnen_state_list[0].split(" ")[0]
                if DEBUG:
                    self.log("Identified trash type: "+trash_type)
                match trash_type:
                    case "RM2": # residual waste
                        # purple
                        self.backlight("800080")
                    case "PPK": # paper
                        # green
                        self.backlight("008000")
                    case "BIO": # bio
                        # brown
                        self.backlight("ff4e030")
                    case "WET": # plastics
                        # yellow
                        self.backlight("FFFF00")
            else:
                # info normal light
                self.backlight()
        except:
            # info normal light
            self.backlight()
    
    def rpyc_close(self):
        # close e131 connection on server to wled
        try:
            self.rpyc_misc.root.close()
        except:
            pass
        
        # close connection
        try:
            self.rpyc_misc.close()
        except:
            pass