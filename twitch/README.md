# Twitch

I have several automations around twitch:

## Twitch Stream still running

To turn off devices when the stream is over, this script regularly checks if the channel is still live.
The script is turned on by the automation which starts the stream after a duration of the usual stream duration minus 10 minutes (to catch possible delays)

### Requires
- Twitch token in `input_text.twitch_api_token`
