# IoT Platform Setup Guide

This guide explains how to set up and run the complete IoT platform to achieve **50% of the project points**.

## Architecture Overview

The system consists of two main parts:

1. **User's Home** (`user/` directory):
   - Temperature sensors (5 rooms)
   - Local MQTT broker (Mosquitto)
   - Gateway (bridges local to cloud)

2. **Cloud Infrastructure** (`cloud/` directory):
   - Cloud MQTT broker
   - Kafka + Zookeeper
   - InfluxDB (time series database)
   - Cloud Ingestor (MQTT → Kafka)
   - Pipeline P1 (Kafka → InfluxDB) - **Worth 25% of points**

## Data Flow

```
[Sensors] → [Local MQTT] → [Gateway] → [Cloud MQTT] → [Ingestor] → [Kafka] → [Pipeline P1] → [InfluxDB]
```

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB of free RAM
- Ports available: 1883, 1884, 8086, 9092

## Step-by-Step Setup

### Step 1: Create the Global Network

The gateway needs a shared network to communicate with cloud services.

```bash
docker network create global_net
```

### Step 2: Start the Cloud Infrastructure

Navigate to the cloud directory and start all cloud services:

```bash
cd cloud
docker-compose up --build
```

This will start:
- Cloud MQTT broker (port 1884)
- Zookeeper (for Kafka)
- Kafka (port 9092)
- InfluxDB (port 8086)
- Cloud Ingestor
- Pipeline P1

**Wait for all services to be ready** (about 30-60 seconds). You should see:
- "Ingestor is running"
- "Pipeline P1 is running"

### Step 3: Start User's Home Sensors

Open a **new terminal** and navigate to the user directory:

```bash
cd user
docker-compose up --build
```

This will start:
- Local MQTT broker (port 1883)
- 5 temperature sensors (room1, room2, room3, living_room, office)
- Gateway

**You should see**:
- Sensors publishing temperature readings every second
- Gateway forwarding messages to cloud
- Ingestor receiving messages and sending to Kafka
- Pipeline P1 saving data to InfluxDB

## Verification

### 1. Check Sensor Data Flow

You should see logs like:

**Gateway:**
```
Forwarded: room1/temperature -> user1/room1/temperature: {"timestamp": "...", "value": 22.5}
```

**Cloud Ingestor:**
```
Sent to Kafka: {'user_id': 'user1', 'room': 'room1', 'timestamp': '...', 'value': 22.5}
```

**Pipeline P1:**
```
Saved to InfluxDB: user_id=user1, room=room1, temperature=22.5, timestamp=...
```

### 2. Query InfluxDB Data

Access InfluxDB UI:
```
http://localhost:8086
```

**Login credentials:**
- Username: `admin`
- Password: `adminpassword`

**To query data:**
1. Go to "Data Explorer"
2. Select bucket: `iot-bucket`
3. Select measurement: `temperature_raw`
4. Click "Submit"

You should see temperature data from all rooms!

**Example Flux query:**
```flux
from(bucket: "iot-bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "temperature_raw")
  |> filter(fn: (r) => r["user_id"] == "user1")
```

### 3. Check Kafka Topics

To verify Kafka is receiving data:

```bash
# List topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Consume messages from the topic
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sensor-raw-data \
  --from-beginning
```

## Stopping the System

### Stop User's Home:
```bash
cd user
docker-compose down
```

### Stop Cloud Infrastructure:
```bash
cd cloud
docker-compose down
```

### Remove the network (optional):
```bash
docker network rm global_net
```

## Troubleshooting

### Gateway can't connect to cloud MQTT

**Problem:** `Failed to connect to cloud MQTT broker`

**Solution:**
1. Ensure cloud services are running: `docker ps`
2. Check if `cloud-mosquitto` container is up
3. Verify global_net exists: `docker network ls`

### Pipeline P1 not saving data

**Problem:** No data appearing in InfluxDB

**Solution:**
1. Check Kafka is receiving data (see verification step 3)
2. Check Pipeline P1 logs: `docker logs pipeline-p1`
3. Verify InfluxDB is running: `docker ps | grep influxdb`

### Port conflicts

**Problem:** `port is already allocated`

**Solution:**
- Stop other services using those ports
- Or modify ports in docker-compose.yml files

## Component Descriptions

### 1. Temperature Sensors
- **Technology:** Python with paho-mqtt
- **Function:** Simulate room temperature with 1:60 time scale
- **Output:** JSON messages with timestamp and temperature value

### 2. Gateway
- **Technology:** Python with paho-mqtt
- **Function:** Bridge between local and cloud MQTT brokers
- **Purpose:** Forward sensor data from user's home to cloud

### 3. Cloud MQTT Broker
- **Technology:** Eclipse Mosquitto 1.6.12
- **Function:** Receive data from multiple user gateways
- **Port:** 1884 (external), 1883 (internal)

### 4. Cloud Ingestor
- **Technology:** Python with paho-mqtt + kafka-python
- **Function:** Subscribe to cloud MQTT and publish to Kafka
- **Purpose:** Bridge MQTT to Kafka for stream processing

### 5. Kafka + Zookeeper
- **Technology:** Confluent Kafka 7.5.0
- **Function:** Distributed streaming platform
- **Purpose:** Decouple data ingestion from processing pipelines

### 6. Pipeline P1 - Save Raw Data 
- **Technology:** Python with kafka-python + influxdb-client
- **Function:** Consume from Kafka and save to InfluxDB
- **Worth:** 25% of project points
- **Data Model:**
  - Measurement: `temperature_raw`
  - Tags: `user_id`, `room`
  - Field: `temperature`
  - Timestamp: from sensor

### 7. InfluxDB
- **Technology:** InfluxDB 2.7
- **Function:** Time series database
- **Purpose:** Store and query sensor data efficiently

## Data Model

### InfluxDB Schema

```
Measurement: temperature_raw
├── Tags (indexed)
│   ├── user_id: "user1"
│   └── room: "room1", "room2", etc.
├── Fields (values)
│   └── temperature: <float>
└── Timestamp: <ISO 8601>
```

**Example data point:**
```json
{
  "measurement": "temperature_raw",
  "tags": {
    "user_id": "user1",
    "room": "room1"
  },
  "fields": {
    "temperature": 22.5
  },
  "timestamp": "2024-11-22T10:30:00Z"
}
```

## Technology Choices

### Why MQTT?
- Lightweight protocol perfect for IoT devices
- Publish/Subscribe pattern decouples producers and consumers
- Low bandwidth and battery usage

### Why Kafka?
- Scalable stream processing
- Fault-tolerant with data replication
- Allows multiple consumers (pipelines) to process same data
- Replay capability for reprocessing

### Why InfluxDB?
- Purpose-built for time series data
- Efficient storage with compression
- Fast queries with indexed tags
- Built-in retention policies
- Flux query language for complex analytics

### Why Python?
- Rich ecosystem for IoT and data processing
- Easy integration with MQTT, Kafka, and InfluxDB
- Clear, readable code for educational purposes

## Project Structure

```
user/
├── docker-compose.yml           # User's home orchestration
├── mqtt_getway/
│   ├── gateway.py              # Gateway implementation
│   ├── Dockerfile
│   └── requirements.txt
└── sensor_temperature/
    ├── controller.py           # Sensor controller
    ├── timeseries_get.py       # Temperature simulator
    ├── Dockerfile
    └── requirements.txt

cloud/
├── docker-compose.yml          # Cloud infrastructure orchestration
├── ingestor/
│   ├── ingestor.py            # MQTT to Kafka bridge
│   ├── Dockerfile
│   └── requirements.txt
└── pipeline-p1/
    ├── pipeline_p1.py         # Kafka to InfluxDB (Raw Data)
    ├── Dockerfile
    └── requirements.txt
```

## What This Achieves

✅ **1st Level Functions [50%]**
- ✅ Devices implemented following specification
- ✅ Gateway receives from MQTT and sends to Cloud
- ✅ Save pipeline implemented and stores data to InfluxDB (25%)

This implementation gives you **50% of the total project points (10/20 points)**.

## Next Steps (for higher grades)

To achieve higher grades, you would need to implement:

**2nd Level Functions [25%]:**
- Pipeline P2: Clean data (remove values of exactly 100°C)
- Pipeline P3: Actuate (send heat pump commands)
- Pipeline P4: Aggregate (calculate mean temperature per user)

**3rd Level Functions [25%]:**
- Handle backpressure in actuate pipeline
- Deploy to Kubernetes (Minikube)

## Time Estimation

Expected time to complete this setup:
- Initial setup and understanding: 1-2 hours
- Implementing components: 4-6 hours
- Testing and debugging: 2-3 hours
- Documentation: 1-2 hours
- **Total: 8-13 hours**
