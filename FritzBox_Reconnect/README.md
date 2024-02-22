# Fritz Reconnect
Since I have DSL at home which required a regular reconnect and the FritzBox used was only capable to put this into a time frame of multiple hours I needed a solutation which does not cut off the internet while doing e.g. backups. 
I turned off this automatic reconnect and just run this AppDaemon script by firing the event `fritz_reconnect` every day at 6a.m.


The used automation is this one (`input_button.fritz_reconnect` is a button to check last actual reconnect to prevent to many reconnects - because the initial schedule was not daily. *You may remove this condition*):
```yaml
alias: FritzBox - Automatic DSL reconnect
description: ""
trigger:
  - platform: time
    at: "06:00:00"
condition:
  - condition: template
    value_template: >-
      {{ (( now().timestamp() -
      as_timestamp(states('input_button.fritz_reconnect')) ) / 3600) > 22 }}
    alias: Check if last reconnect was at least 22h ago
  - condition: template
    value_template: >-
      {{ not is_state('device_tracker.X', 'home') and not
      is_state('person.X', 'home') }}
    alias: Only reconnect if laptop not connected and person not home
action:
  - event: fritz_reconnect
    event_data: {}
mode: single

```