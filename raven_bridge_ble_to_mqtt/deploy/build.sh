#!/bin/bash
mkdir bridgebletomqtt/
mkdir bridgebletomqtt/lib/
mkdir bridgebletomqtt/lib/systemd/
mkdir bridgebletomqtt/lib/systemd/system/
mkdir bridgebletomqtt/opt/
mkdir bridgebletomqtt/opt/raven_bridge_ble_to_mqtt
chmod -R 755 bridgebletomqtt
cp ../bridgebletomqtt.service bridgebletomqtt/lib/systemd/system
cp ../*.txt bridgebletomqtt/opt/raven_bridge_ble_to_mqtt
cp ../*.py bridgebletomqtt/opt/raven_bridge_ble_to_mqtt
cp -R ../DEBIAN bridgebletomqtt
chmod 644 bridgebletomqtt/lib/systemd/system/*
chmod 644 bridgebletomqtt/opt/raven_bridge_ble_to_mqtt/*
#chown -R root:root bridgebletomqtt
dpkg-deb --build bridgebletomqtt
lintian bridgebletomqtt.deb
rm -R bridgebletomqtt
