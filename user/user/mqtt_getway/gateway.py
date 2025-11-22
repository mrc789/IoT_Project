import os
import time
import paho.mqtt.client as mqtt
import json

# Configuration from environment variables
LOCAL_MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
CLOUD_MQTT_HOST = os.getenv("CLOUD_MQTT_HOST", "cloud-mosquitto")
CLOUD_MQTT_PORT = int(os.getenv("CLOUD_MQTT_PORT", "1883"))
USER_ID = os.getenv("USER_ID", "user1")

# MQTT clients
local_client = None
cloud_client = None

def on_local_message(client, userdata, message):
    """
    Callback when a message is received from local MQTT broker.
    Forwards the message to the cloud MQTT broker.
    """
    try:
        topic = message.topic
        payload = message.payload.decode("utf-8")

        # Parse the message to validate it's proper JSON
        data = json.loads(payload)

        # Create cloud topic: user_id/original_topic
        cloud_topic = f"{USER_ID}/{topic}"

        # Forward to cloud
        cloud_client.publish(cloud_topic, payload)
        print(f"Forwarded: {topic} -> {cloud_topic}: {payload}")

    except Exception as e:
        print(f"Error processing message: {e}")

def on_local_connect(client, userdata, flags, rc):
    """Callback when connected to local MQTT broker"""
    if rc == 0:
        print(f"Connected to local MQTT broker at {LOCAL_MQTT_HOST}")
        # Subscribe to all temperature topics from all rooms
        client.subscribe("#")
        print("Subscribed to all topics (#)")
    else:
        print(f"Failed to connect to local MQTT broker, return code {rc}")

def on_cloud_connect(client, userdata, flags, rc):
    """Callback when connected to cloud MQTT broker"""
    if rc == 0:
        print(f"Connected to cloud MQTT broker at {CLOUD_MQTT_HOST}")
    else:
        print(f"Failed to connect to cloud MQTT broker, return code {rc}")

def main():
    global local_client, cloud_client

    print("Starting Gateway...")
    print(f"Local MQTT: {LOCAL_MQTT_HOST}")
    print(f"Cloud MQTT: {CLOUD_MQTT_HOST}:{CLOUD_MQTT_PORT}")
    print(f"User ID: {USER_ID}")

    # Create cloud MQTT client
    cloud_client = mqtt.Client(client_id=f"gateway-{USER_ID}-cloud")
    cloud_client.on_connect = on_cloud_connect

    # Create local MQTT client
    local_client = mqtt.Client(client_id=f"gateway-{USER_ID}-local")
    local_client.on_connect = on_local_connect
    local_client.on_message = on_local_message

    # Connect to cloud MQTT broker first
    try:
        cloud_client.connect(CLOUD_MQTT_HOST, CLOUD_MQTT_PORT, 60)
        cloud_client.loop_start()
        print("Cloud MQTT client loop started")
    except Exception as e:
        print(f"Error connecting to cloud MQTT: {e}")
        return

    # Connect to local MQTT broker
    try:
        local_client.connect(LOCAL_MQTT_HOST, 1883, 60)
        local_client.loop_start()
        print("Local MQTT client loop started")
    except Exception as e:
        print(f"Error connecting to local MQTT: {e}")
        return

    # Keep the gateway running
    print("Gateway is running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down gateway...")
        local_client.loop_stop()
        cloud_client.loop_stop()
        local_client.disconnect()
        cloud_client.disconnect()
        print("Gateway stopped.")

if __name__ == "__main__":
    main()
