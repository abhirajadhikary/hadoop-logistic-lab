#!/bin/bash

docker exec kafka bash -c '

if [ ! -f /opt/kafka/kraft-combined-logs/meta.properties ]
then
/opt/kafka/bin/kafka-storage.sh format \
-t MkU3OEVBNTcwNTJENDM2Qk \
-c /opt/kafka/config/server.properties
fi

nohup /opt/kafka/bin/kafka-server-start.sh \
/opt/kafka/config/server.properties \
>/tmp/kafka.log 2>&1 &
'

echo "Kafka Started"