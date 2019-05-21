from kafka import KafkaProducer
from config import *

producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)

def start():
    return

def stop():   
    producer.close()
    producer.flush()
    
def publish(topic, msg):
    producer.send(topic, bytearray(msg,'utf8'))
    