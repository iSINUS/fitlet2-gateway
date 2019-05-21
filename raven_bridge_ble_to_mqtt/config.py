import os
DEVICE_HOST = os.uname()[1]

CLIENT_ID = DEVICE_HOST+".adv"
TOPIC_PREFIX = "fluke/BLEtoMQTT/"+DEVICE_HOST             #MQTT prefix to identify this device
TOPIC_PREFIX_INFLUX = "fluke/BLEtoMQTT/influx/"+DEVICE_HOST 

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

KAFKA_BOOTSTRAP = ""
KAFKA_TOPIC = "bletomqtt"