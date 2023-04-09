#!/usr/bin/env python3

"""InfluxDB monitoring relay for rtl_433."""

# rtl_433/examples/rtl_433_influxdb_relay.py

# Start rtl_433 (rtl_433 -F syslog::1433), then this script

# Option: PEP 3143 - Standard daemon process library
# (use Python 3.x or pip install python-daemon)
# import daemon

from __future__ import print_function
from __future__ import with_statement

from influxdb import InfluxDBClient
import socket
from datetime import datetime
import json
import sys
import configparser
import argparse
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(dir_path + "/relay.ini")

UDP_IP            = config['UDP']['HOST'] if 'HOST' in config['UDP'] else "127.0.0.1"
UDP_PORT          = config['UDP']['PORT'] if 'PORT' in config['UDP'] else 1433
INFLUXDB_HOST     = config['INFLUXDB']['HOST'] if 'HOST' in config['INFLUXDB'] else "127.0.0.1"
INFLUXDB_PORT     = config['INFLUXDB']['PORT'] if 'PORT' in config['INFLUXDB'] else 8086
INFLUXDB_USERNAME = config['INFLUXDB']['USERNAME'] if 'USERNAME' in config['INFLUXDB'] else ""
INFLUXDB_PASSWORD = config['INFLUXDB']['PASSWORD'] if 'PASSWORD' in config['INFLUXDB'] else ""
INFLUXDB_DATABASE = config['INFLUXDB']['DATABASE'] if 'DATABASE' in config['INFLUXDB'] else "rtl433"

TAGS = [
    "channel",
    "id",
    #"label", # mapped below
]

FIELDS = [
    "temperature_C",
    "humidity",
    "battery_ok",
    "pressure_hPa",
]

# User defined labels
CHANNEL_LABELS = {
    "A": config['LABELS']['CHANNEL_A'] if 'CHANNEL_A' in config['LABELS'] else "",
    "B": config['LABELS']['CHANNEL_B'] if 'CHANNEL_B' in config['LABELS'] else "",
    "C": config['LABELS']['CHANNEL_C'] if 'CHANNEL_C' in config['LABELS'] else "",
}

parser = argparse.ArgumentParser(description="relay messages from rtl-433 to influxdb with added labels")
parser.add_argument(
    "-v", "--verbose", dest="verbose", action="store_true", help="print relay messages to stdout"
)
parser.add_argument(
    "-n", "--dry-run", dest="dry_run", action="store_true", help="do not send to influxdb"
)
args = parser.parse_args()
VERBOSE = args.verbose
DRY_RUN = args.dry_run

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.bind((UDP_IP, UDP_PORT))


def sanitize(text):
    return text.replace(" ", "_").replace("/", "_").replace(".", "_").replace("&", "")


def parse_syslog(line):
    """Try to extract the payload from a syslog line."""
    line = line.decode("ascii")  # also UTF-8 if BOM
    if line.startswith("<"):
        # fields should be "<PRI>VER", timestamp, hostname, command, pid, mid, sdata, payload
        fields = line.split(None, 7)
        line = fields[-1]
    return line


def rtl_433_probe():
    if not DRY_RUN:
        client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT,
                            username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD,
                            database=INFLUXDB_DATABASE)

    while True:
        line, _addr = sock.recvfrom(1024)

        try:
            line = parse_syslog(line)
            data = json.loads(line)

            # input should be unixtime seconds.usec
            # output must be either unixtime in NANOSEC(10^9) or an ISO string
            timestamp = int(float(data["time"]) * 1000000000)
            if not "model" in data:
                continue
            measurement = sanitize(data["model"])

            tags = {}
            for tag in TAGS:
                if tag in data:
                    tags[tag] = data[tag]

            fields = {}
            for field in FIELDS:
                if field in data:
                    fields[field] = data[field]

            if len(fields) == 0:
                continue

            # Map labels
            tags["label"] = CHANNEL_LABELS[tags["channel"]]

            # Fix formats to match pre-existing DB definition
            fields["battery_ok"] = float(fields["battery_ok"])
            fields["humidity"] = float(fields["humidity"])

            point = {
                "measurement": measurement,
                "time": timestamp, # datetime.now().isoformat(),
                "tags": tags,
                "fields": fields,
            }

            if VERBOSE:
                print(point)
            try:
                if not DRY_RUN:
                    client.write_points([point])
            except Exception as e:
                print("error {} writing {}".format(e, point), file=sys.stderr)

        except KeyError:
            pass

        except ValueError:
            pass


def run():
    # with daemon.DaemonContext(files_preserve=[sock]):
    #  detach_process=True
    #  uid
    #  gid
    #  working_directory
    rtl_433_probe()


if __name__ == "__main__":
    run()
