#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import mqtt
import kafka_producer
import json
import aioblescan
from math import pow
import time
from config import *

from ctypes import c_uint32, c_uint8, c_uint16, Union, LittleEndianStructure

class BLE_READING_FIELDS(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('measurement', c_uint32, 21),
        ('state', c_uint32, 4),
        ('decimal_places', c_uint32, 3),
        ('magnitude', c_uint32, 3),
        ('sign', c_uint32, 1)
    ]

class BLE_ATTRIB_FIELDS(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('_range', c_uint16, 7),
        ('range_decade', c_uint16, 3),
        ('attribute', c_uint16, 5), 
        ('capture_flag', c_uint16, 1)
    ]

class uReadingFields(Union):
    _pack_ = 1
    _fields_ = [("reading", c_uint32), ("readingFields", BLE_READING_FIELDS)]

class uAttribFields(Union):
    _pack_ = 1
    _fields_ = [("attrib", c_uint16), ("attribFields", BLE_ATTRIB_FIELDS)]

class BLE_READING(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('company_id', c_uint16, 16),
        ('battery', c_uint8, 8),
        ('read', uReadingFields),
        ('unit', c_uint8),
        ('function', c_uint8),
        ('attr', uAttribFields),
        # statistics
        ('log_unit', c_uint8, 8),
        ('log_reading_dp_avg', c_uint8, 2),
        ('log_reading_magnitude_avg', c_uint8, 3),
        ('log_reading_status_avg', c_uint8, 3),
        ('log_reading_dp_max', c_uint8, 2),
        ('log_reading_magnitude_max', c_uint8, 3),
        ('log_reading_status_max', c_uint8, 3),
        ('log_reading_dp_min', c_uint8, 2),
        ('log_reading_magnitude_min', c_uint8, 3),
        ('log_reading_status_min', c_uint8, 3),
        ('average_reading', c_uint16, 16),
        ('max_reading', c_uint16, 16),
        ('min_reading', c_uint16, 16),
        #('max_time', c_uint32, 32),
        #('min_time', c_uint32, 32)
        ('FW_VERSION_MAJOR',c_uint8),
        ('FW_VERSION_MINOR',c_uint8),
        ('FW_VERSION_SUBMINOR',c_uint8),
        ('SW_VERSION_MAJOR',c_uint8),
        ('SW_VERSION_MINOR',c_uint8),
        ('SW_VERSION_SUBMINOR',c_uint8),
        ('advertizing', c_uint16, 16)
    ]

# FLUKE Sensors Models
FLUKE_SENSORS = {
                1:'FLUKE 3510FC',
                2:'FLUKE 3511FC',
                3:'FLUKE 3520FC',
                4:'FLUKE 3521FC',
                7:'FLUKE 3530FC',
                8:'FLUKE 3530FC',
                9:'FLUKE 3530FC',
                10:'FLUKE 3530FC'
                }

FLUKE_SENSORS_STATE = {
                0: "normal",
                1: "blank",
                2: "inactive",
                3: "----",
                4: "OL",
                5: "OL",
                6: "Open",
                7: "Discharge",
                8: "Leads",
                9: "greater than",
                10: "missing phase",
                11: "error",
                12: "less than",
                13: "disconnected"
                }

BLE_READING_MAGNITUDE = {
                0: 0,
                1: 9,
                2: 6,
                3: 3,
                4: -3,
                5: -6,
                6: -9, 
                7: -12,
                8: 12, 
                9: 15
                }

BLE_READING_UNIT = {
                0: "none",
                1: "V AC",
                2: "V DC",
                3: "A AC",
                4: "A DC",
                5: "Hz",
                6: "rH pct",
                7: "\u00B0C",
                8: "\u00B0F",
                9: "ranK",
                10: "K",
                11: "\u2126",
                12: "S",
                13: "duty %",
                14: "sec",
                15: "F",
                16: "dB",
                17: "dBM",
                18: "W",
                19: "J",
                20: "H",
                21: "PSI",
                22: "m",
                23: "in",
                24: "ft",
                25: "m H2O",
                26: "in H2)",
                27: "in H2O",
                28: "Bar",
                29: "Pa",
                30: "g/cm2",
                31: "dBV",
                32: "CF+",
                33: "V AC+DC",
                34: "A AC+DC",
                35: "%",
                36: "VAC/Hz",
                37: "ɡ",
                38: "m/s^2",
                39: "in/s",
                40: "mm/s",
                41: "mils",
                42: "µm",
                43: "Unknown"
                }

class Fluke(object):

     def decode(self,packet):
        result={}
        rssi=packet.retrieve("rssi")
        if rssi:
            result["rssi"]=rssi[-1].val
        power=packet.retrieve("tx_power")
        if power:
            result["tx_power"]=power[-1].val
        try:
            payload=packet.retrieve("Payload for mfg_specific_data")
            if payload:
                val=payload[0].val
                s = BLE_READING.from_buffer(bytearray(val))
                if s.company_id==0x025e:
                    #Looks just right
                    result["mac"]=packet.retrieve("peer")[0].val
                    result["battery"]=s.battery

                    result["measurments"]=s.read.readingFields.measurement
                    result["state"]=FLUKE_SENSORS_STATE[s.read.readingFields.state]
                    result["decimalPlaces"]=s.read.readingFields.decimal_places
                    result["magnitude"]=BLE_READING_MAGNITUDE[s.read.readingFields.magnitude]
                    result["sign"]=s.read.readingFields.sign
                    result["type"]=FLUKE_SENSORS[s.unit]
                    result["unit"]=BLE_READING_UNIT[s.unit]

                    result["average_reading"]=s.average_reading
                    result["max_reading"]=s.max_reading
                    result["min_reading"]=s.min_reading

                    power = result["magnitude"]-result["decimalPlaces"]
                    multiplier = pow(10, power)
                    value = result["measurments"]*multiplier
                    if (result["sign"]!=0): value = -value
                    result["value"]=value   
                    result["advertizing"]=250
                    if s.advertizing!=0:
                        result["advertizing"]=s.advertizing
                    result["fw_version"]= "%i.%i.%i" % (s.FW_VERSION_MAJOR,s.FW_VERSION_MINOR,s.FW_VERSION_SUBMINOR)
                    result["sw_version"]= "%i.%i.%i" % (s.SW_VERSION_MAJOR,s.SW_VERSION_MINOR,s.SW_VERSION_SUBMINOR)
                    return result
                else:
                    return None
            else:
                return None
        except:
            return None


def process(data):
    ev=aioblescan.HCI_Event()
    xx=ev.decode(data)
    sensor_mac = ev.retrieve("peer")
       
    xx=Fluke().decode(ev)
    
    if xx:
        #send results via MQTT
        mqtt.publish(TOPIC_PREFIX + "/" +sensor_mac[0].val+  "/data", json.dumps(xx))        
        pattern = '%s,sensor_mac=%s,sensor_type=%s,sensor_unit=%s,sensor_sw_version=%s,sensor_fw_version=%s sensor_value=%.'+str(xx['decimalPlaces'])+'f,sensor_rssi=%i,sensor_battery=%i,sensor_adv=%i %i'
        output = (pattern % (DEVICE_HOST,xx['mac'],xx['type'].replace(" ","\ "),xx['unit'].replace(" ","\ "),xx['sw_version'],xx['fw_version'],xx['value'],xx['rssi'],xx['battery'],xx['advertizing'],time.time()*1000000000))
        mqtt.publish(TOPIC_PREFIX_INFLUX + "/" +xx['mac']+  "/data", output)
        output = (pattern % (DEVICE_HOST+"_kafka",xx['mac'],xx['type'].replace(" ","\ "),xx['unit'].replace(" ","\ "),xx['sw_version'],xx['fw_version'],xx['value'],xx['rssi'],xx['battery'],xx['advertizing'],time.time()*1000000000))
        kafka_producer.publish(KAFKA_TOPIC,output)
        #print(output)
