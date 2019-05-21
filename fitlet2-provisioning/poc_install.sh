#!/bin/bash
echo "Start installation ..."
WIFI_SSID=""
WIFI_PASS=""
INFLUXDB_CLOUD=""
INFLUXDB_USER=""
INFLUXDB_PASS=""

#Upgrade system
echo "Upgrade system"
apt update
apt -y upgrade
#Install cockpit
echo "Install cockpit"
apt -y install cockpit

#Install bluez, pip, libfontconfig
echo "Install bluez, pip, libfontconfig, mc"
apt -y install bluez
apt -y install python3-pip
apt -y install mc
apt -y install libfontconfig

#Remove cloud-init
echo "Remove cloud-init"
echo 'datasource_list: [ None ]' | -s tee /etc/cloud/cloud.cfg.d/90_dpkg.cfg
apt -y purge cloud-init
rm -rf /etc/cloud/; rm -rf /var/lib/cloud/

#Remove netplan
echo "Remove netplan"
apt -y install ifupdown
cat << EOF_interfaces >/etc/network/interfaces
# ifupdown has been replaced by netplan(5) on this system.  See
# /etc/netplan for current configuration.
# To re-enable ifupdown on this system, you can run:
#    apt install ifupdown
allow-hotplug enp2s0
iface enp2s0 inet dhcp

allow-hotplug enp3s0
iface enp3s0 inet dhcp

auto lo
iface lo inet loopback

auto wlp1s0
allow-hotplug wlp1s0
iface wlp1s0 inet static
	hostapd /etc/hostapd/hostapd.conf
	address 192.168.1.1
	netmask 255.255.255.0

EOF_interfaces

systemctl stop networkd-dispatcher
systemctl disable networkd-dispatcher
systemctl mask networkd-dispatcher
apt -y purge nplan netplan.io
apt -y install --reinstall network-manager
systemctl disable NetworkManager-wait-online.service
systemctl mask NetworkManager-wait-online.service

#Configure WiFi AP
echo "Configure WiFi AP"
systemctl disable wpa_supplicant
systemctl stop wpa_supplicant
systemctl mask wpa_supplicant
apt -y install hostapd
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> /etc/default/hostapd
cat << EOF_hostapd >/etc/hostapd/hostapd.conf
interface=wlp1s0
ssid=$WIFI_SSID
hw_mode=g
channel=11
wpa=3
wpa_passphrase=$WIFI_PASS
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
auth_algs=1
macaddr_acl=0

EOF_hostapd

cat << EOF_rclocal >/etc/rc.local
#!/bin/bash
sudo ifdown wlp1s0
sudo ifup wlp1s0
sleep 3
sudo ifdown wlp1s0
sudo ifup wlp1s0
exit 0

EOF_rclocal
chmod +x /etc/rc.local

apt install dnsmasq
cat << EOF_dnsmasq >>/etc/dnsmasq.conf
interface=lo,wlp1s0
no-dhcp-interface=lo
dhcp-range=192.168.1.10,192.168.1.100,255.255.255.0,12h

EOF_dnsmasq
sed -i -e 's/After=network.target/After=network-online.target/g' /lib/systemd/system/rc-local.service
sed -i -e 's/After=network.target/After=rc-local.service/g' /lib/systemd/system/dnsmasq.service
sed -i -e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/g' /etc/sysctl.conf

#Configure reverse ssh
. "poc_reversessh.sh"

#Install mosquitto
echo "Install mosquitto"
apt -y install mosquitto

#Install TICK
echo "Install Influxdb"
wget -nc https://dl.influxdata.com/influxdb/releases/influxdb_1.5.4_amd64.deb
dpkg -i influxdb_1.5.4_amd64.deb
service influxdb start
echo "Install Telegraf"

wget -nc https://dl.influxdata.com/telegraf/releases/telegraf_1.7.1-1_amd64.deb
dpkg -i telegraf_1.7.1-1_amd64.deb
cat << EOF_telegraf > /etc/telegraf/telegraf.conf
[agent]
  interval = "5s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000
  collection_jitter = "0s"
  flush_interval = "10s"
  flush_jitter = "0s"
  precision = ""
  debug = false
  quiet = false
  logfile = "/var/log/telegraf/telegraf.log"
  hostname = ""
  omit_hostname = false

[[outputs.influxdb]]
  urls = ["http://127.0.0.1:8086"]
  database = "telegraf"

[[inputs.mqtt_consumer]]
  servers = ["tcp://localhost:1883"]
  qos = 2
  connection_timeout = "10s"
  topics = [
    "fluke/BLEtoMQTT/influx/+/+/data",
  ]
  persistent_session = true
  client_id = "telegraf"
  data_format = "influx"

EOF_telegraf
cat << EOF_telegraf_cloud > /etc/telegraf/telegraf_cloud.conf
[agent]
  interval = "5s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 100000000
  collection_jitter = "0s"
  flush_interval = "10s"
  flush_jitter = "0s"
  precision = ""
  debug = false
  quiet = false
  logfile = "/var/log/telegraf/telegraf_cloud.log"
  hostname = ""
  omit_hostname = false

[[outputs.influxdb]]
  urls = ["$INFLUXDB_CLOUD"]
  database = "telegraf_raven"
  username = "$INFLUXDB_USER"
  password = "$INFLUXDB_PASS"
  insecure_skip_verify = true

[[inputs.mqtt_consumer]]
  servers = ["tcp://localhost:1883"]
  qos = 2
  connection_timeout = "10s"
  topics = [
    "fluke/BLEtoMQTT/influx/+/+/data",
  ]
  persistent_session = true
  client_id = "telegraf_cloud"
  data_format = "influx"

EOF_telegraf_cloud

cat << EOF_telegraf_cloud_service > /lib/systemd/system/telegraf_cloud.service
[Unit]
Description=The plugin-driven server agent for reporting metrics into InfluxDB
Documentation=https://github.com/influxdata/telegraf
After=network.target

[Service]
EnvironmentFile=-/etc/default/telegraf
User=telegraf
ExecStart=/usr/bin/telegraf -config /etc/telegraf/telegraf_cloud.conf -config-directory /etc/telegraf/telegraf.d $TELEGRAF_OPTS
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartForceExitStatus=SIGPIPE
KillMode=control-group

[Install]
WantedBy=multi-user.target

EOF_telegraf_cloud_service
systemctl daemon-reload
systemctl enable telegraf_cloud.service

echo "Install Chronograf"
wget -nc https://dl.influxdata.com/chronograf/releases/chronograf_1.5.0.1_amd64.deb
dpkg -i chronograf_1.5.0.1_amd64.deb

echo "Install Kapacitor"
wget -nc https://dl.influxdata.com/kapacitor/releases/kapacitor_1.5.0_amd64.deb
dpkg -i kapacitor_1.5.0_amd64.deb

#Install Grafana
echo "Install Grafana"
apt --fix-broken -y install
wget -nc https://s3-us-west-2.amazonaws.com/grafana-releases/release/grafana_5.2.1_amd64.deb
dpkg -i grafana_5.2.1_amd64.deb
systemctl enable grafana-server.service
grafana-cli plugins install snuids-radar-panel
service grafana-server.service restart

#Install Bridge BLE to MQTT
echo "Install Bridge BLE to MQTT"
apt --fix-broken -y install
dpkg -i bridgebletomqtt.deb

echo "Cockpit: " && service cockpit status | grep Active:
echo "dnsmasq: " && service dnsmasq status | grep Active:
echo "Autossh: " && service autossh status | grep Active:
echo "mosquitto: " && service cockpit status | grep Active:
echo "InfluxDB: " && service influxdb status | grep Active:
echo "Telegraf: " && service telegraf status | grep Active:
echo "Telegraf to CLoud: " && service telegraf_cloud status | grep Active:
echo "Chronograf: " && service chronograf status | grep Active:
echo "Kapacitor: " && service kapacitor status | grep Active:
echo "Grafana: " && service grafana-server status | grep Active:
echo "Bridge BLE to MQTT: " && service bridgebletomqtt status | grep Active:
echo "Network: " && ip addr show | grep 'inet '
