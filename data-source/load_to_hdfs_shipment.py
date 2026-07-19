import json
from kafka import KafkaConsumer
from hdfs import InsecureClient

# Initialize HDFS Client (pointing to your running namenode container)
hdfs_client = InsecureClient('http://localhost:9870', user='root')
hdfs_path = '/bronze/logistics/shipment_events.json'

# Initialize Kafka Consumer
consumer = KafkaConsumer(
    'shipment-events',
    bootstrap_servers=['localhost:29092'],
    auto_offset_reset='earliest',
    api_version=(2, 5, 0),
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print(f"Listening for events on Kafka topic 'shipment-events'...")

for message in consumer:
    event_data = message.value
    print(f"Received from Kafka: {event_data.get('shipment_id', 'Unknown')}")
    
    # Append the record directly to your HDFS bronze layer
    try:
        # Convert dictionary to line-delimited JSON string
        json_line = json.dumps(event_data) + "\n"
        
        if hdfs_client.status(hdfs_path, strict=False) is None:
            hdfs_client.write(hdfs_path, data=json_line, encoding='utf-8')
        else:
            hdfs_client.write(hdfs_path, data=json_line, encoding='utf-8', append=True)
            
        print(f"Successfully uploaded to HDFS path: {hdfs_path}")
    except Exception as e:
        print(f"Failed writing to HDFS: {e}")