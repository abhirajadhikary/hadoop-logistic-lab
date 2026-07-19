#!/bin/bash

set -e

echo
echo "========================================"
echo "Starting Kafka"
echo "========================================"

./ingestion/kafka/start_kafka.sh

sleep 8

echo
echo "========================================"
echo "Verifying Kafka"
echo "========================================"

./ingestion/kafka/verify_kafka.sh

echo
echo "========================================"
echo "Creating Topic"
echo "========================================"

./ingestion/kafka/create_topics.sh

echo
echo "========================================"
echo "Available Topics"
echo "========================================"

./ingestion/kafka/list_topics.sh

echo
echo "========================================"
echo "Describing Topic"
echo "========================================"

./ingestion/kafka/describe_topics.sh

echo
echo "========================================"
echo "Producing Messages to Topic"
echo "========================================"

./ingestion/kafka/producer.sh

echo 
echo "========================================"
echo "Sample Data Sent to Topic"
echo "========================================"

./ingestion/kafka/send_demo_data.sh

echo
echo "========================================"
echo "Consuming Messages from Topic"
echo "========================================"

./ingestion/kafka/consumer.sh

echo
echo "========================================"
echo "Stop Kafka"
echo "========================================"

./ingestion/kafka/stop_kafka.sh