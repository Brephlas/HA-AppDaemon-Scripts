# Spotify LedFX Update Scene

I have a RGB LED strip around the ceiling in my office which is used for music visualization from LedFX. To have more suitable effects for different speeds of songs I used this script which gets the songs properties from spotify (hence needs custom app in developer dashboard in Spotify) and then decides which mode to use.

The REST call used inside the script is as follows:

```yaml
ledfx_scene_by_id:
  url: "http://<LedFX-Server-IP>:8888/api/scenes"
  method: "put"
  content_type: "application/json"
  payload: '{"id":"{{name}}","action":"activate"}'
```