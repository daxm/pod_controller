#!/usr/bin/env bash

echo "Start docker-compose build and launch containers if successful."
docker-compose up --build --detach --remove-orphans
docker image prune -a -f
