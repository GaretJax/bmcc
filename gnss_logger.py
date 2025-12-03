#!/usr/bin/env python3

import argparse
import os
import threading
from queue import Queue

import requests


URL = "https://bmcc.local.aldryn.net/tracking/api/{}/ping/"

try:
    from serial import Serial as SerialPort
except ImportError:
    import termios
    # Zero-dependencies serial port code copied from:
    # https://github.com/wiseman/arduino-serial/blob/master/arduinoserial.py
    #
    # Original license included here
    #
    # Copyright 2007 John Wiseman <jjwiseman@yahoo.com>
    #
    # Permission is hereby granted, free of charge, to any person
    # obtaining a copy of this software and associated documentation files
    # (the "Software"), to deal in the Software without restriction,
    # including without limitation the rights to use, copy, modify, merge,
    # publish, distribute, sublicense, and/or sell copies of the Software,
    # and to permit persons to whom the Software is furnished to do so,
    # subject to the following conditions:
    #
    # The above copyright notice and this permission notice shall be
    # included in all copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    # EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    # MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    # NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
    # BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
    # ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    # CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    # SOFTWARE.
    #
    # Map from the numbers to the termios constants (which are pretty much
    # the same numbers).

    BPS_SYMS = {
        4800: termios.B4800,
        9600: termios.B9600,
        19200: termios.B19200,
        38400: termios.B38400,
        57600: termios.B57600,
        115200: termios.B115200,
    }

    # Indices into the termios tuple.

    IFLAG = 0
    OFLAG = 1
    CFLAG = 2
    LFLAG = 3
    ISPEED = 4
    OSPEED = 5
    CC = 6

    def bps_to_termios_sym(bps):
        return BPS_SYMS[bps]

    class SerialPort:
        """Represents a serial port connected to an Arduino."""

        def __init__(self, serialport, bps):
            """Takes the string name of the serial port (e.g.
            "/dev/tty.usbserial","COM1") and a baud rate (bps) and connects to
            that port at that speed and 8N1. Opens the port in fully raw mode
            so you can send binary data.
            """
            self.fd = os.open(serialport, os.O_RDWR | os.O_NOCTTY | os.O_NDELAY)
            self.fh = os.fdopen(self.fd, "rb")
            attrs = termios.tcgetattr(self.fd)
            bps_sym = bps_to_termios_sym(bps)
            # Set I/O speed.
            attrs[ISPEED] = bps_sym
            attrs[OSPEED] = bps_sym

            # 8N1
            attrs[CFLAG] &= ~termios.PARENB
            attrs[CFLAG] &= ~termios.CSTOPB
            attrs[CFLAG] &= ~termios.CSIZE
            attrs[CFLAG] |= termios.CS8
            # No flow control
            attrs[CFLAG] &= ~termios.CRTSCTS

            # Turn on READ & ignore contrll lines.
            attrs[CFLAG] |= termios.CREAD | termios.CLOCAL
            # Turn off software flow control.
            attrs[IFLAG] &= ~(termios.IXON | termios.IXOFF | termios.IXANY)

            # Make raw.
            attrs[LFLAG] &= ~(
                termios.ICANON | termios.ECHO | termios.ECHOE | termios.ISIG
            )
            attrs[OFLAG] &= ~termios.OPOST

            # It's complicated--See
            # http://unixwiz.net/techtips/termios-vmin-vtime.html
            attrs[CC][termios.VMIN] = 0
            attrs[CC][termios.VTIME] = 20
            termios.tcsetattr(self.fd, termios.TCSANOW, attrs)

        def readline(self):
            return self.fh.readline()

        def close(self):
            os.close(self.fd)


def parse_line(line):
    s = line.strip()
    ts, rest = s.split(",", 1)
    payload, rssi, snr, freq_err = rest.rsplit(",", 3)
    return ts, payload, rssi, snr, freq_err


def main():
    ap = argparse.ArgumentParser(description="GNSS serial logger")
    ap.add_argument(
        "--port", required=True, help="Serial port (e.g., COM5 or /dev/tty.usbmodem*)"
    )
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--out", required=True, help="Output logging path")
    ap.add_argument("--beacon", required=True, help="Beacon ID")
    args = ap.parse_args()

    # Open serial
    ser = SerialPort(args.port, args.baud)
    state = {"running": True}

    # Shared state
    queue = Queue()
    url = URL.format(args.beacon)

    def process():
        while state["running"]:
            raw = queue.get()

            fields = [
                "msg_id",
                "utc_ts",
                "lat",
                "lat_dir",
                "lon",
                "lon_dir",
                "strength",
                "sats",
                "hdop",
                "alt",
                "alt_unit",
                "geoid_sep",
                "geoid_sep_unit",
                "dgps_age",
                "dgps_ref_id",
            ]

            msg, sep, check = raw.partition("*")
            if not sep:
                print(f"Checksum not found: {raw}")
                continue

            try:
                payload = zip(fields, msg.split(","), strict=True)
            except Exception:
                print(f"Could not parse message: {raw}")
                continue

            try:
                latitude, longitude, altitude = (
                    float(payload["lat"]),
                    float(payload["lon"]),
                    float(payload["alt"]),
                )
            except Exception:
                print(f"Could not parse position: {raw}")
                continue

            requests.post(
                url,
                json={
                    "latitude": latitude,
                    "longitude": longitude,
                    "altitude": altitude,
                },
            )

    t = threading.Thread(target=process, daemon=True)
    t.start()

    with open(args.out, "a", newline="") as f:
        try:
            while state["running"]:
                raw = ser.readline().decode(errors="ignore").strip()
                if not raw:
                    continue
                f.write(raw)
                f.write("\n")
                f.flush()
                print(raw)
                queue.put(raw)
        except KeyboardInterrupt:
            pass
        finally:
            state["running"] = False


if __name__ == "__main__":
    main()
