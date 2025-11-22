import os
import time
import json
import paho.mqtt.client as mqtt
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configuration from environment variables
MQTT_HOST = os.getenv("MQTT_HOST", "cloud-mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sensor-raw-data")

# Kafka producer
producer = None

def on_mqtt_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        # Subscribe to all topics from all users
        client.subscribe("#")
        print("Subscribed to all topics (#)")
    else:
        print(f"Failed to connect to MQTT broker, return code {rc}")

def on_mqtt_message(client, userdata, message):
    """
    Callback when a message is received from MQTT.
    Forwards the message to Kafka.
    """
    try:
        topic = message.topic
        payload = message.payload.decode("utf-8")

        # Parse the message to validate it's proper JSON
        data = json.loads(payload)

        # Extract user_id and room from topic (format: user_id/room/temperature)
        topic_parts = topic.split("/")
        if len(topic_parts) >= 2:
            user_id = topic_parts[0]
            room = topic_parts[1]
        else:
            user_id = "unknown"
            room = "unknown"

        # Enrich the message with metadata
        enriched_data = {
            "user_id": user_id,
            "room": room,
            "timestamp": data.get("timestamp"),
            "value": data.get("value"),
            "raw_topic": topic
        }

        # Send to Kafka
        future = producer.send(KAFKA_TOPIC, value=enriched_data)

        # Wait for confirmation (optional, but good for reliability)
        record_metadata = future.get(timeout=10)

        print(f"Sent to Kafka: {enriched_data}")
        print(f"  Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")

    except json.JSONDecodeError as e:
        print(f"Invalid JSON in message: {payload}, Error: {e}")
    except KafkaError as e:
        print(f"Kafka error: {e}")
    except Exception as e:
        print(f"Error processing message: {e}")

def main():
    global producer

    print("Starting Cloud Ingestor...")
    print(f"MQTT: {MQTT_HOST}:{MQTT_PORT}")
    print(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Kafka Topic: {KAFKA_TOPIC}")

    # Wait for Kafka to be ready
    print("Waiting for Kafka to be ready...")
    time.sleep(10)

    # Create Kafka producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',  # Wait for all replicas to acknowledge
            retries=3
        )
        print("Kafka producer created successfully")
    except Exception as e:
        print(f"Error creating Kafka producer: {e}")
        return

    # Create MQTT client
    mqtt_client = mqtt.Client(client_id="cloud-ingestor")
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message

    # Connect to MQTT broker
    try:
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("MQTT client loop started")
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        return

    # Keep the ingestor running
    print("Ingestor is running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down ingestor...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        producer.close()
        print("Ingestor stopped.")

if __name__ == "__main__":
    main()
