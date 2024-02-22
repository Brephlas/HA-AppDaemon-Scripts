# PiAware

I live near an airport, so a lot of airplanes crosses by - at times every few minutes actually. Since this is extremely annoying when listening to media while the window is open (e.g. summer weather and you want to start to cool down the living rooms), I wanted to have a solution other than pausing or adjusting the volume manually each time.

I found piaware, set this one up and wrote an Appdaemon script for home assistant, which queries the piaware instance every 10 seconds for nearby airplanes. When it detects airplanes that are in a specific range around my home and still flying at low altitudes it increases the volume of all active media players specified in the script itself. After the airplane is far enough the volume is decreased again to the old volume level.

For the volume adjustment I used the script [HA-Fade-Volume-Script from MaxVRAM 2](https://github.com/MaxVRAM/HA-Fade-Volume-Script) This allows seamless adjustment (previously had this in steps, this can be quite overwhelming).

Since I thought this could be useful for some others, I wanted to share the script.
If you want to use this, you need to adjust the HOME location to your coordinates, the `MEDIA_PLAYERS` that should be adjusted, as well as the IP address of your piaware instance.

For improved adjustements you can adjust the `HEIGHT` and `DISTANCE` in which the flights are included in further action. Also you can adjust the `VOLUME_MODIFIER` which regulates the strength of the adjustment.
Also, for each media_player you can set up special conditions (+ attributes) which must be fulfilled for volume adjustment (such as open window sensors).