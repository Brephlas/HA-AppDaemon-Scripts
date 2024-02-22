import appdaemon.plugins.hass.hassapi as hass
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor, DeviceType
from time import sleep

DEBUG = False


class OpenRGB(hass.Hass):
    def initialize(self):
        self.listen_event(self.default, "openrgb_default")
        self.listen_event(self.stripe, "openrgb_stripe")
        self.listen_event(self.doorbell, "openrgb_doorbell")
        self.listen_event(self.hardwaresync, "openrgb_hardwaresync")
        self.listen_event(self.co2, "openrgb_co2")
        
    def connect(self):
        ## init client
        if not hasattr(self, 'client'):
            self.restart_myself()
            self.client = OpenRGBClient('<IP-Address-of-OpenRGB-Host>', 6742, 'hass-python-api')
            self.motherboard = self.client.get_devices_by_type(DeviceType.MOTHERBOARD)[0]

        # Motherboard zones:
        # [Zone(name=Aura Mainboard, id=0), Zone(name=Aura Addressable 1, id=1), Zone(name=Aura Addressable 2, id=2), Zone(name=Aura Addressable 3, id=3)]

    def restart_myself(self):
        self.restart_app("OpenRGB")

    def hex_to_rgb(self, hexa):
        return tuple(int(hexa[i:i+2], 16)  for i in (0, 2, 4))

    def default(self, event, data, args):
        self.connect()
        self.motherboard.set_mode('static')
        self.motherboard.set_color(RGBColor(0,0,255))

    def doorbell(self, event, data, args):
        self.connect()
        self.motherboard.set_mode('flashing')
        self.client.load_profile('doorbell')

    def hardwaresync(self, event, data, args):
        self.connect()
        self.motherboard.set_mode('direct')
        self.client.load_profile('hardwaresync')

    def co2(self, event, data, args):
        self.connect()
        self.motherboard.set_mode('flashing')
        co2 = data['co2']
        if co2:
            if co2 < 500:
                r,g,b = (0, 255, 0)
            if co2 > 500:
                r,g,b = (255, 68, 0)
            if co2 > 1000:
                r,g,b = (255, 0, 0)
        self.motherboard.set_color(RGBColor(r,g,b))
        sleep(5)
        self.hardwaresync(event, data, args)

    def stripe(self, event, data, args):
        self.connect()
        self.motherboard.set_mode('direct')
        if data['rgb']:
            r,g,b = self.hex_to_rgb(data['rgb'])
        else:
            r = 255
            g = 0
            b = 0
        self.motherboard.zones[1].set_color(RGBColor(r, g, b))