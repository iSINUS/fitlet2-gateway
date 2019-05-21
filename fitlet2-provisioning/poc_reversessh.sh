#!/bin/bash
echo "Configure reverse ssh"
MASTER_SSH_IP=""
MASTER_SSH_USER=""
SLAVE_SSH_PORT=""

apt update
apt -y install autossh
mkdir /home/fluke
mkdir /home/fluke/.ssh
echo '-----BEGIN RSA PRIVATE KEY-----

-----END RSA PRIVATE KEY-----' > /home/fluke/.ssh/id_rsa
chown -R fluke:fluke /home/fluke
chmod 600 /home/fluke/.ssh/id_rsa

cat << EOF_autossh >/lib/systemd/system/autossh.service
[Unit]
Description=Keeps a reverse shh tunnel to '$MASTER_SSH_IP' open
After=network.target

[Service]
User=fluke
Environment="AUTOSSH_GATETIME=0"
ExecStart=/usr/bin/autossh -TN -M 0 -o "ExitOnForwardFailure=yes" -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -o "StrictHostKeyChecking=no" $MASTER_SSH_USER@$MASTER_SSH_IP -R $SLAVE_SSH_PORT:127.0.0.1:22 -i /home/fluke/.ssh/id_rsa

[Install]
WantedBy=multi-user.target

EOF_autossh

systemctl daemon-reload
systemctl start autossh.service
systemctl enable autossh.service
