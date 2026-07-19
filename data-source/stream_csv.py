import csv
import json
import time
from kafka import KafkaProducer

# Connect to the Kafka broker running in your Docker container
producer = KafkaProducer(
    bootstrap_servers=['localhost:29092'],
    api_version=(2, 5, 0),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

csv_file_path = 'dataset/tracking_events.csv'
topic_name = 'logistic-events'

print(f"Starting stream from {csv_file_path} to Kafka topic '{topic_name}'...")

try:
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        # DictReader automatically turns each CSV row into a Python dictionary
        csv_reader = csv.DictReader(file)
        
        for row in csv_reader:
            # Clean up whitespace from keys and values
            clean_row = {key.strip(): value.strip() for key, value in row.items()}
            
            # Publish row data to Kafka
            producer.send(topic_name, value=clean_row)
            print(f"Sent event to Kafka: {clean_row.get('event_id', 'Unknown ID')}")
            
            # Wait 1 second before sending the next line to simulate continuous streaming
            time.sleep(1) 

except FileNotFoundError:
    print(f"Error: Could not find the file at {csv_file_path}. Make sure you run the script from the project root directory.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    producer.flush()
    print("Streaming session finished.")