# rtl-433-influxdb-relay

Relay rtl-433 messages to InfluxDB with added context labels

Designed for AcuRite wireless measurements.

Based off [rtl-433/examples/rtl_433_influxdb_relay.py](https://github.com/merbanan/rtl_433/blob/master/examples/rtl_433_influxdb_relay.py)

## rtl-433

config
```
rtl_433.conf.sample
```

### FreeBSD daemon
daemon:
```
rc.d/rtl-433
```

rc.conf:
```
rtl_433_enable="YES"
```

## relay

config
```
relay.ini.sample
```

### FreeBSD daemon
daemon:
```
rc.d/rtl_433_influxdb_relay
```

rc.conf:
```
rtl_433_influxdb_relay_enable="YES"
```
