import os
DEVICE_HOST = os.uname()[1]

CLIENT_ID = DEVICE_HOST+".adv"
TOPIC_PREFIX = "fluke/BLEtoMQTT/"+DEVICE_HOST             #MQTT prefix to identify this device
TOPIC_PREFIX_INFLUX = "fluke/BLEtoMQTT/influx/"+DEVICE_HOST 

MQTT_HOST = ""
MQTT_PORT = 8883
MQTT_USER = ""
MQTT_PASS = ""
MQTT_KEEPALIVE = 60
