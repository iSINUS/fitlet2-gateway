import paho.mqtt.client as mqtt
import fluke
import json
import ssl
from config import *

client = mqtt.Client(client_id=CLIENT_ID, clean_session=False)

def on_connect(client, userdata, flags, rc): 
        #notify MQTT subscribers that gateway is online
        client.publish(TOPIC_PREFIX, "online", qos=1)

def start():
    client.on_connect = on_connect
   
    client.max_inflight_messages_set(24000)
    client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
    print("Connected to:",MQTT_HOST, MQTT_PORT)

    client.loop_start()

def stop():
    #notify MQTT subscribers that gateway is offline
    publish(TOPIC_PREFIX, "offline")
            
def publish(topic, msg):
    client.publish(topic, msg, qos=1)