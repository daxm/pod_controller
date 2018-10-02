#!/usr/bin/env bash

echo "### Remove any previously installed Docker packages ###"
sudo apt remove docker*

echo "### Add APT Cert and Key ###"
sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88

echo "### Add Docker Repository ###"
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

echo "### Refresh APT Cache ###"
sudo apt update

echo "### Install Docker CE ###"
sudo apt install docker-ce -y

echo "### Install Python3 and associated packages and modules for Docker Compose. ###"
echo "Ensure Universe repository is enabled."
sudo apt add-apt-repository universe
sudo apt install python3 python3-pip python3-setuptools -y
sudo -H pip3 install docker-compose

echo "### Add current user to the docker group.  (Log out and back in to take effect.) ###"
sudo usermod -aG docker $(whoami)

echo "Copy .env-example to .env."
cd flask
if [ ! -f .env ]; then
  cp .env-example .env
fi
cd ..

echo "Copy userdata.yml-example to userdata.yml."
cd flask
if [ ! -f .userdata.yml ]; then
  cp userdata.yml-example userdata.yml
fi
cd ..

echo "########### NEXT STEPS ############"
echo "### 1.  Edit the flash/.env and modify it to your environment."
echo "### 2.  Edit the flash/userdata.yml and modify it to your environment."
echo "### 3.  Run the runme.sh file to build, deploy, and start the Docker container."
echo "###################################"
