# Weather Forecast

I wanted specific sensors for the maximum forecast values for wind speed, temperature and cloud coverage (also now easily extendable). I know that this could've been done a lot easier, but for me this solution works better. Also, this now stores the time for which the highest value is expected

To get the content into `sensor.home_forecast_hourly` the following template sensor can be used:
```yaml
- trigger:
    - platform: time_pattern
      hours: /1
  action:
    - service: weather.get_forecasts
      data:
        type: hourly
      target:
        entity_id: weather.openweathermap
      response_variable: hourly
  sensor:
    - name: Home Forecast Hourly
      unique_id: "forecast"
      state: "{{ hourly['weather.openweathermap'].forecast[0].condition }}"
      attributes:
        forecast: "{{ hourly['weather.openweathermap'].forecast }}"

```