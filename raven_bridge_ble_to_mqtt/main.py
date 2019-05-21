import mqtt
import kafka_producer
import fluke
import asyncio
import aioblescan
from config import *

event_loop = asyncio.get_event_loop()

#First create and configure a raw socket hci0
mysocket = aioblescan.create_bt_socket(0)

#create a connection with the raw socket
#fac=event_loop.create_connection(aioblescan.BLEScanRequester,sock=mysocket)
fac = event_loop._create_connection_transport(mysocket,aioblescan.BLEScanRequester,None,None)

#Start it
conn,btctrl = event_loop.run_until_complete(fac)
#Attach your processing
btctrl.process=fluke.process

btctrl.send_scan_request()

try:
    mqtt.start()
    kafka_producer.start()
    event_loop.run_forever()
except KeyboardInterrupt:
    print('keyboard interrupt')
finally:
    mqtt.stop()
    kafka_producer.stop()
    
    btctrl.stop_scan_request()
    conn.close()
    event_loop.close()
