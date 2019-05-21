# bridge-ble-to-mqtt

The bridge-ble-to-mqtt is designed to provide a generic bridge between BLE devices and a MQTT broker. It allows to scan for BLE devices and send their data to MQTT.

## Installation
```
sudo pip3 install pygatt paho-mqtt pexpect retrying aiohttp kafka-python
setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`
```

## Start
```
sudo python3 main.py
```

## Load on boot
- git clone to **/opt/**
- Copy file **bridgebletomqtt.service** to /lib/systemd/system/ 
- Reload systemd using command:
```
systemctl daemon-reload 
```
- Enable auto start using command:
```
systemctl enable bridgebletomqtt.service
``` 

## MQTT publish
- fluke/BLEtoMQTT/GATEWAY_HOST **online**
- fluke/BLEtoMQTT/GATEWAY_HOST **offline**
- fluke/BLEtoMQTT/GATEWAY_HOST/SENSOR_MAC/data **JSON**
- fluke/BLEtoMQTT/influx/GATEWAY_HOST/SENSOR_MAC/data **InfluxDB Line Protocol**
