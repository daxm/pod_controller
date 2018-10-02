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
sudo add-apt-repository universe
sudo apt install python3 python3-pip python3-setuptools -y
sudo -H pip3 install docker-compose

echo ""
echo "### Add current user to the docker group.  (Log out and back in to take effect.) ###"
sudo usermod -aG docker $(whoami)
echo ""

if [ ! -f ./flask/.env ]; then
  echo "Copy .env-example to .env."
  cp ./flask/.env-example ./flask/.env
fi

if [ ! -f ./flask/.userdata.yml ]; then
  echo "Copy userdata.yml-example to userdata.yml."
  cp ./flask/userdata.yml-example ./flask/userdata.yml
fi

echo "########### NEXT STEPS ############"
echo "1.  Log out and back in to refresh your group associations."
echo "2.  Edit the flash/.env and modify it to your environment."
echo "3.  Edit the flash/userdata.yml and modify it to your environment."
echo "4.  Run the runme.sh file to build, deploy, and start the Docker containers."
echo "###################################"
