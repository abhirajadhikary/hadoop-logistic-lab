#!/bin/bash

docker exec kafka bash -c "

pkill -f kafka.Kafka || true

"

echo "Kafka Stopped"