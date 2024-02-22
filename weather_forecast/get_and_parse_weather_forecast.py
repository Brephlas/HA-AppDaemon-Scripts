import appdaemon.plugins.hass.hassapi as hass
import yaml
from datetime import datetime, time
from pathlib import Path

# {'namespace': 'default', 'domain': 'weather', 'service': 'get_forecasts'}
DEBUG = True

class GetAndParseWeatherForecast(hass.Hass):
    def initialize(self):
      runtime = time(0, 1, 0)
      self.run_hourly(self.parse, runtime)

    def parse(self, event, data, args):
      #weather_response = self.call_service("weather/get_forecasts", entity_id="weather.openweathermap", type="hourly")
      #parsed = yaml.safe_load(weather)
      #weather = parsed['forecast']
      weather = self.get_state("sensor.home_forecast_hourly", attribute="forecast")
      now_time = datetime.now()

      # pull previous values if existent
      # temperature
      try:
        highest_temperature_today = self.get_state('sensor.appdaemon_highest_temperature_today')
        highest_temperature_time = self.get_state('sensor.appdaemon_highest_temperature_today', attribute="time")
      except:
        highest_temperature_today = 0
        highest_temperature_time = None
      # wind speed
      try:
        highest_wind_speed_today = self.get_state('sensor.appdaemon_highest_wind_speed_today')
        highest_wind_speed_time = self.get_state('sensor.appdaemon_highest_wind_speed_today', attribute="time")
      except:
        highest_wind_speed_today = 0
        highest_wind_speed_time = None
      # cloud coverage
      try:
        highest_cloud_coverage_today = self.get_state('sensor.appdaemon_highest_cloud_coverage_today')
        highest_cloud_coverage_time = self.get_state('sensor.appdaemon_highest_cloud_coverage_today', attribute="time")
      except:
        highest_cloud_coverage_today = 0
        highest_cloud_coverage_time = None

      for forecast in weather:
        dt = datetime.strptime(forecast['datetime'], "%Y-%m-%dT%H:%M:%S+00:00")
        if dt.day == now_time.day and dt.hour > now_time.hour:
          # get highest temperature
          forecast_temperature = float(forecast['temperature'])
          if forecast_temperature > highest_temperature_today:
            highest_temperature_today = forecast_temperature
            highest_temperature_time = dt.time()
          # get highest wind speed
          forecast_wind_speed = float(forecast['wind_speed'])
          if forecast_wind_speed > highest_wind_speed_today:
            highest_wind_speed_today = forecast_wind_speed
            highest_wind_speed_time = dt.time()
          # get highest cloud coverage
          forecast_cloud_coverage = float(forecast['cloud_coverage'])
          if forecast_cloud_coverage > highest_cloud_coverage_today:
            highest_cloud_coverage_today = forecast_cloud_coverage
            highest_cloud_coverage_time = dt.time()

      # logging
      if DEBUG:
        self.log("Hoechste festgestellte Temperatur: "+str(highest_temperature_today))
        self.log(highest_temperature_time)
        self.log("Hoechste festgestellte Windgeschwindigkeit: "+str(highest_wind_speed_today))
        self.log(highest_wind_speed_time)
        self.log("Hoechste festgestellte Wolkendeckung: "+str(highest_cloud_coverage_today))
        self.log(highest_cloud_coverage_time)

      # set sensors
      self.set_state("sensor.appdaemon_highest_temperature_today", state = float(highest_temperature_today), attributes = {"friendly_name": "Heutige Höchsttemperatur", "time": highest_temperature_time})
      self.set_state("sensor.appdaemon_highest_wind_speed_today", state = float(highest_wind_speed_today), attributes = {"friendly_name": "Heutige höchste Windgeschwindigkeit", "time": highest_wind_speed_time})
      self.set_state("sensor.appdaemon_highest_cloud_coverage_today", state = float(highest_cloud_coverage_today), attributes = {"friendly_name": "Heutige höchste Wolkendeckung", "time": highest_cloud_coverage_time})
