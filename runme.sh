#!/usr/bin/env bash

echo "Start docker-compose build and launch containers if successful."
sudo docker-compose up --build --detach --remove-orphans
sudo docker image prune -a -f
