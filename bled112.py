#
# Original work Copyright (c) 2014 Danny Zhu
# Modified work Copyright (c) 2017 Alvaro Villoslada
# Modified work Copyright (c) 2017 Fernando Cosentino
# Modified work Copyright (c) 2018 Matthias Gazzari
# Modified work Copyright (c) 2021 retact
#
# Licensed under the MIT license. See the LICENSE file for details.
#

import struct
import threading
import time
import re
import logging
import serial
from serial.tools import list_ports

LOG = logging.getLogger(__name__)

class Packet():
    '''BLED112 packet representation'''

    def __init__(self, ords):
        self.typ = ords[0]
        self.cls = ords[2]
        self.cmd = ords[3]
        self.payload = bytes(ords[4:])

    def __repr__(self):
        return 'Packet(%02X, %02X, %02X, [%s])' % \
            (self.typ, self.cls, self.cmd,
             ' '.join('%02X' % b for b in list(self.payload)))


class BLED112():
    '''Non-Myo-specific Bluetooth backend using the provided BLED112 dongle with pyserial.'''

    def __init__(self, tty):
        if tty is None:
            tty = self._detect_tty()
        if tty is None:
            raise ValueError('Bluegiga BLED112 dongle not found!')
        self.conn = None
        self.ser = serial.Serial(port=tty, baudrate=9600, dsrdtr=1)
        self.buf = []
        self.lock = threading.Lock()
        self._internal_handler = None
        self._external_handler = None

    @staticmethod
    def _detect_tty():
        '''Try to find a Bluegiga BLED112 dongle'''
        for port, desc, hwid in list_ports.comports():
            if re.search(r'PID=2458:0*1', hwid):
                LOG.debug('using "%s" at port %s', desc, port)
                return port
        return None

    # internal data-handling methods
    def recv_packet(self, timeout=None):
        t0 = time.time()
        self.ser.timeout = None
        while timeout is None or time.time() < t0 + timeout:
            if timeout is not None:
                self.ser.timeout = t0 + timeout - time.time()
            c = self.ser.read()
            if not c:
                return None

            ret = self._proc_byte(ord(c))
            if ret:
                if ret.typ == 0x80:
                    self._handle_event(ret)
                return ret

    def _proc_byte(self, c):
        if not self.buf:
            if c in [0x00, 0x80, 0x08, 0x88]:  # [BLE response pkt, BLE event pkt, wifi response pkt, wifi event pkt]
                self.buf.append(c)
            return None
        elif len(self.buf) == 1:
            self.buf.append(c)
            self.packet_len = 4 + (self.buf[0] & 0x07) + self.buf[1]
            return None
        else:
            self.buf.append(c)

        if self.packet_len and len(self.buf) == self.packet_len:
            p = Packet(self.buf)
            self.buf = []
            return p
        return None

    @property
    def handler(self):
        return self._external_handler

    @handler.setter
    def handler(self, func):
        # wrap the provided handler function to be able to process BLED112 packets
        def wrapped_handle_data(packet):
            if (packet.cls, packet.cmd) != (4, 5):
                return
            _, attr, _ = struct.unpack('<BHB', packet.payload[:4])
            pay = packet.payload[5:]
            func(attr, pay)
        self._external_handler = wrapped_handle_data if callable(func) else None

    def _handle_event(self, p):
        if self._internal_handler:
            self._internal_handler(p)
        if self._external_handler:
            self._external_handler(p)

    def _wait_event(self, cls, cmd):
        res = [None]

        def h(p):
            if p.cls == cls and p.cmd == cmd:
                res[0] = p
        self._internal_handler = h
        while res[0] is None:
            self.recv_packet()
        self._internal_handler = None
        return res[0]

    # specific BLE commands
    def scan(self, target_uuid, target_address=None):
        # stop scanning and terminate previous connection 0, 1 and 2
        self._send_command(6, 4)
        for connection_number in range(3):
            self._send_command(3, 0, struct.pack('<B', connection_number))

        # start scanning
        LOG.info('scanning for devices...')
        self._send_command(6, 2, b'\x01')
        while True:
            packet = self.recv_packet()
            if packet.payload.endswith(bytes.fromhex(target_uuid)):
                address = list(list(packet.payload[2:8]))
                address_string = ':'.join(format(item, '02x') for item in reversed(address))
                LOG.debug('found a Bluetooth device (MAC address: %s)', address_string)
                if target_address is None or target_address.lower() == address_string:
                    # stop scanning and return the found mac address
                    self._send_command(6, 4)
                    return address_string

    def connect(self, target_address):
        address = [int(item, 16) for item in reversed(target_address.split(':'))]
        conn_pkt = self._send_command(6, 3, struct.pack('<6sBHHHH', bytes(address), 0, 6, 6, 64, 0))
        self.conn = list(conn_pkt.payload)[-1]
        self._wait_event(3, 0)

    def disconnect(self):
        if self.conn is not None:
            return self._send_command(3, 0, struct.pack('<B', self.conn))
        return None

    def read_attr(self, attr):
        if self.conn is not None:
            self._send_command(4, 4, struct.pack('<BH', self.conn, attr))
            ble_payload = self._wait_event(4, 5).payload
            # strip off the 4 byte L2CAP header and the payload length byte of the ble payload field
            return ble_payload[5:]
        return None

    def write_attr(self, attr, val, wait_response=True):
        if self.conn is not None:
            self._send_command(4, 5, struct.pack('<BHB', self.conn, attr, len(val)) + val)
            if wait_response:
                ble_payload = self._wait_event(4, 1).payload
                # strip off the 4 byte L2CAP header and the payload length byte of the ble payload field
                return ble_payload[5:]
        return None

    def _send_command(self, cls, cmd, payload=b''):
        s = struct.pack('<4B', 0, len(payload), cls, cmd) + payload
        self.ser.write(s)

        while True:
            p = self.recv_packet()
            # no timeout, so p won't be None
            if p.typ == 0:
                return p
            # not a response: must be an event
            self._handle_event(p)
