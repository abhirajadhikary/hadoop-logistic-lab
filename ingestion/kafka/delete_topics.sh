#!/bin/bash

docker exec kafka kafka-topics.sh \
--bootstrap-server localhost:9092 \
--delete \
--topic test-topic