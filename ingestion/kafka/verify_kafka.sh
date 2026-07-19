#!/bin/bash

echo
echo "========== Container =========="
docker ps | grep kafka

echo
echo "========== Kafka Process =========="
docker exec kafka ps -ef | grep kafka.Kafka

echo
echo "========== Broker =========="
docker exec kafka kafka-broker-api-versions.sh \
--bootstrap-server localhost:9092