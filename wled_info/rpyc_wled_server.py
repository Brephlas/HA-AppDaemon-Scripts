from e131 import e131
from utils import *
import rpyc
from rpyc.utils.server import ThreadedServer

class WLEDInfo(rpyc.Service):
    led_num = 120
    e131 = None

    def on_connect(self, conn):
        self.e131 = e131(120)
        self.data = None
        self.set_ip("<IP-Address-of-receiving-WLED-instance>")

    def on_disconnect(self, conn):
        self.exposed_close()

    def exposed_clear_leds(self):
        self.set_leds(np.zeros(self.led_num))

    def exposed_close(self):
        self.exposed_clear_leds()
        self.e131.close()

    def display_led(self):
        area_tmp = np.append(self.area1, self.area2)
        data = area_tmp.flatten()
        self.set_leds(data)

    def hex_to_rgb(self, hexa):
        return tuple(int(hexa[i:i+2], 16)  for i in (0, 2, 4))

    def exposed_nightlight(self, *args, **kwargs):
        zeroes = np.array([[0,0,0] for h in range(0, int(self.led_num-20))])
        data = np.array(
            [[253, 244, 220] for h in range(0, 10)]) # nightlight itself

        """mode 0:default 1:lower_end-only"""
        try:
            mode = kwargs['mode']
        except:
            mode = 0

        trash_hex = kwargs['trash_hex']
        if trash_hex != 0 and mode != 1:
            # color dependent on trash type coming from HA
            r,g,b = self.hex_to_rgb(trash_hex)
        else:
            r,g,b = (0,0,0)
        upper_lights = np.array([[int(r),int(g),int(b)] for h in range(0, int(20))])
        data = np.append(data, zeroes)
        data = np.append(data, upper_lights)

        # calculate color of led for current outside temperature
        temperature_led = kwargs['temperature_led']
        current_outside_temperature = int((int(temperature_led)-20)/2)
        r,g,b = (0,0,0)
        if current_outside_temperature > 30:
            r,g,b = self.hex_to_rgb("FF0000") # red
        elif current_outside_temperature > 20:
            r,g,b = self.hex_to_rgb("ffff00") # yellow
        elif current_outside_temperature > 0:
            r,g,b = self.hex_to_rgb("00FF00") # green
        else:
            r,g,b = self.hex_to_rgb("bbbbbb") # white

        # calculate color of forecast led
        forecast_led = kwargs['forecast_led']

        # temperature_led *3 (because of 3 colors) + color mode
        if mode != 1:
            # set temperature led
            data[(int(temperature_led) * 3) + 0] = r
            data[(int(temperature_led) * 3) + 1] = g
            data[(int(temperature_led) * 3) + 2] = b

            # set forecast led
            if int(temperature_led) != int(forecast_led) and abs(int(temperature_led) - int(forecast_led)) > 4:
                f_r,f_g,f_b = self.hex_to_rgb("800080") # purple
                data[(int(forecast_led) * 3) + 0] = int(f_r/4)
                data[(int(forecast_led) * 3) + 1] = int(f_g/4)
                data[(int(forecast_led) * 3) + 2] = int(f_b/4)

            temperature_inside = kwargs['temperature_inside']
            if int(temperature_inside) != int(temperature_led) and int(temperature_inside) != int(forecast_led):
                i_r,i_g,i_b = self.hex_to_rgb("0000FF") # blue
                data[(int(temperature_inside)*3) + 0] = i_r
                data[(int(temperature_inside)*3) + 1] = i_g
                data[(int(temperature_inside)*3) + 2] = i_b

            if kwargs['biomuell']:
                biomuell_led = 109*3
                r,g,b = self.hex_to_rgb("964B00") # brown
                data[biomuell_led+0] = int(r/4)
                data[biomuell_led+1] = int(g/4)
                data[biomuell_led+2] = int(b/4)

        # send data to e131 stream
        data = data.flatten()
        self.set_leds(data)

    """
    ### other functions
    """

    def set_leds(self, data: np.ndarray):
        # cap brightness
        self.e131.send_data(data*min(50, 100)/100)

    def interpolate_distance_from_speakers(self, x):
        return np.clip(np.minimum(abs(x - self.gvars.speaker1.get()), abs(x - self.gvars.speaker2.get())), 0,
                       self.led_num - 2)  # clipped to led_num-2 to avoid IndexError in audio_speakers when speed = 0

    def set_ip(self, ip: str):
        self.e131.set_ip(ip)

if __name__ == "__main__":
    t = ThreadedServer(WLEDInfo, port=18861)
    t.start()