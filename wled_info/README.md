# WLED Info

I have a WLED LED strip (120 LEDs) at my front door which should function as a nightlight when going trough the corridor but also is used for several other tasks, such as showing the weather forecast temperatures as well as the current inside/outside temperatures as single LEDs (`get_and_parse_weather_forecast.py` is used to get the respective values).

`rpyc_wled_server.py` server is running on a separate host to translate the data coming from AppDaemon to actual E131 data (as this was too complex inside AppDaemon itself - especially due to the time this script should be left running).

*Uses https://github.com/Hilicot/WLED_E131_PC_Client* 


An Aqara waterleak sensor is used with pressure pad to detect bed occupation
```yaml
- platform: history_stats
  name: History stats Bett belegt (kurz)
  entity_id: binary_sensor.aqara_waterleak_pressure_sensor_bed_water_leak
  state: "on"
  type: time
  end: "{{ now() }}"
  duration:
    minutes: 5
```

To display reminders for trash cans which needs to be placed to the street, waste_collection_schedule is used:
```yaml
- platform: waste_collection_schedule #used in general automation
  name: tonnenbutton
  count: 4
  value_template: '{{value.types|join(", ")}}|{{value.daysTo}}|{{value.date.strftime("%d.%m.%Y")}}}}'
  date_template: '{{value.date.strftime("%d.%m.%Y")}}'
```

## Example other use cases
- Using MQTT this LED is also used to display timers running on google home devices.