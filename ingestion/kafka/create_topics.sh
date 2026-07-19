#!/bin/bash

docker exec kafka kafka-topics.sh \
--bootstrap-server localhost:9092 \
--create \
--topic test-topic \
--partitions 3 \
--replication-factor 3

echo "Topic Created"