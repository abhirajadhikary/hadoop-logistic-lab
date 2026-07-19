#!/bin/bash

for i in {1..40}
do
    echo "Order-$i"
done | docker exec -i kafka \
kafka-console-producer.sh \
--bootstrap-server localhost:9092 \
--topic test-topic