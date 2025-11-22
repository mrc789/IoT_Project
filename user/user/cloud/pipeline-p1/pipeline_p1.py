import os
import time
import json
from kafka import KafkaConsumer
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

# Configuration from environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sensor-raw-data")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "pipeline-p1-group")

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-super-secret-auth-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "iot-org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "iot-bucket")

def main():
    print("Starting Pipeline P1 - Save Raw Data...")
    print(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Kafka Topic: {KAFKA_TOPIC}")
    print(f"Kafka Group ID: {KAFKA_GROUP_ID}")
    print(f"InfluxDB: {INFLUXDB_URL}")
    print(f"InfluxDB Org: {INFLUXDB_ORG}")
    print(f"InfluxDB Bucket: {INFLUXDB_BUCKET}")

    # Wait for services to be ready
    print("Waiting for Kafka and InfluxDB to be ready...")
    time.sleep(15)

    # Create InfluxDB client
    try:
        influx_client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        print("InfluxDB client created successfully")
    except Exception as e:
        print(f"Error creating InfluxDB client: {e}")
        return

    # Create Kafka consumer
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=KAFKA_GROUP_ID,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',  # Start from the beginning if no offset
            enable_auto_commit=True
        )
        print("Kafka consumer created successfully")
    except Exception as e:
        print(f"Error creating Kafka consumer: {e}")
        return

    print("Pipeline P1 is running. Waiting for messages...")

    # Process messages
    try:
        for message in consumer:
            try:
                data = message.value
                print(f"Received message: {data}")

                # Extract data
                user_id = data.get("user_id", "unknown")
                room = data.get("room", "unknown")
                timestamp_str = data.get("timestamp")
                temperature = data.get("value")

                # Parse timestamp
                if timestamp_str:
                    try:
                        # Parse ISO format timestamp
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except Exception as e:
                        print(f"Error parsing timestamp: {e}, using current time")
                        timestamp = datetime.utcnow()
                else:
                    timestamp = datetime.utcnow()

                # Create InfluxDB point
                # Measurement: temperature_raw
                # Tags: user_id, room (for efficient querying)
                # Fields: temperature (the actual value)
                # Time: from sensor
                point = Point("temperature_raw") \
                    .tag("user_id", user_id) \
                    .tag("room", room) \
                    .field("temperature", float(temperature)) \
                    .time(timestamp)

                # Write to InfluxDB
                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
                print(f"Saved to InfluxDB: user_id={user_id}, room={room}, temperature={temperature}, timestamp={timestamp}")

            except Exception as e:
                print(f"Error processing message: {e}")
                continue

    except KeyboardInterrupt:
        print("\nShutting down Pipeline P1...")
    finally:
        consumer.close()
        influx_client.close()
        print("Pipeline P1 stopped.")

if __name__ == "__main__":
    main()
