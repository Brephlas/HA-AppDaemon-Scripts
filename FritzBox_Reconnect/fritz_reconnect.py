from __future__ import print_function
import appdaemon.plugins.hass.hassapi as hass
import argparse
from contextlib import closing
import socket

DEFAULT_HOST = '192.168.178.1'
DEFAULT_PORT = 49000

URL_PATH = '/igdupnp/control/WANIPConn1'

def create_http_request():
    body = create_http_body()

    return '\r\n'.join([
        'POST {} HTTP/1.1'.format(URL_PATH),
        'Host: {0}:{1:d}'.format(DEFAULT_HOST, DEFAULT_PORT),
        'SoapAction: urn:schemas-upnp-org:service:WANIPConnection:1#ForceTermination',
        'Content-Type: text/xml; charset="utf-8"',
        'Content-Length: {:d}'.format(len(body)),
        '',
        body,
    ])


def create_http_body():
    return '\r\n'.join([
        '<?xml version="1.0" encoding="utf-8"?>',
        '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">',
        '  <s:Body>',
        '    <u:ForceTermination xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"/>',
        '  </s:Body>',
        '</s:Envelope>',
    ])

class FritzReconnect(hass.Hass):
        def initialize(self):
            self.listen_event(self.run, "fritz_reconnect")

        def run(self, event, data, args):
            """Connect to the box and submit SOAP data via HTTP."""
            request_data = create_http_request()

            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                s.connect((DEFAULT_HOST, DEFAULT_PORT))
                s.send(request_data.encode())