#!/bin/bash

docker exec -it kafka \
kafka-console-producer.sh \
--bootstrap-server localhost:9092 \
--topic test-topic