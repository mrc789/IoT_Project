# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a complete IoT platform that simulates temperature sensors in a user's home and processes data through a cloud infrastructure. The system demonstrates a real-world IoT architecture with MQTT, Kafka, and time-series database storage. Time is simulated at a 1:60 ratio (1 second real time = 1 minute simulated time).

**Two-part architecture:**
1. **User's Home** (`user/`): Sensors, local MQTT broker, gateway
2. **Cloud Infrastructure** (`cloud/`): Cloud MQTT, Kafka, InfluxDB, processing pipelines

## Architecture

### Core Components

1. **Temperature Sensors (sensor_temperature/)**: Dockerized Python services that simulate room temperature based on:
   - Current simulated time (hour of day, month)
   - Heatpump status (on/off)
   - Room temperature tracking with heating/cooling physics
   - 20% outlier ratio for testing anomaly detection

2. **MQTT Communication**:
   - **Mosquitto broker**: Central message broker running on port 1883
   - **Data topic pattern**: `{room_name}/temperature` - publishes readings as JSON: `{"timestamp": "yyyy-mm-ddTHH:MM:SS.sss", "value": <float>}`
   - **Control topic pattern**: `{room_name}/heatpump` - receives commands as JSON: `{"status": <1 or 0>}`

3. **Timeseries Simulators (timeseries_get.py)**:
   - `TemperatureSimulator`: Simulates room temperature with seasonal and daily variations
   - `PresenceSimulator`: Simulates room occupancy based on time and day of week
   - Both classes track simulated time internally with 1:60 time acceleration

4. **Gateway (mqtt_getway/)**: Bridges local MQTT to cloud MQTT, forwarding all sensor data to cloud infrastructure

5. **Cloud Ingestor (cloud/ingestor/)**: MQTT to Kafka bridge that enriches messages with metadata

6. **Pipeline P1 (cloud/pipeline-p1/)**: Kafka consumer that saves raw sensor data to InfluxDB

7. **InfluxDB**: Time-series database storing sensor readings with tags (user_id, room) and fields (temperature)

8. **Kafka + Zookeeper**: Distributed streaming platform enabling multiple processing pipelines

### Data Flow

```
[Sensors] → [Local MQTT] → [Gateway] → [Cloud MQTT] → [Ingestor] → [Kafka] → [Pipeline P1] → [InfluxDB]
                                                                         ↓
                                                              (Future: P2, P3, P4)
```

### Docker Architecture

**User's Home:**
- **internal_net**: Bridge network connecting all sensors and local mosquitto
- **global_net**: External network connecting gateway to cloud services
- Multiple room services (room1, room2, room3, living_room, office) built from sensor_temperature image

**Cloud:**
- **global_net**: Shared network for all cloud services
- Services: cloud-mosquitto, zookeeper, kafka, influxdb, ingestor, pipeline-p1

## Commands

### Running the Complete System

**IMPORTANT:** The system requires starting cloud services BEFORE user's home services.

```bash
# 1. Create the global network (only once)
docker network create global_net

# 2. Start cloud infrastructure (Terminal 1)
cd cloud
docker-compose up --build

# 3. Start user's home (Terminal 2, wait for cloud to be ready)
cd user
docker-compose up --build

# Stop cloud services
cd cloud && docker-compose down

# Stop user's home
cd user && docker-compose down

# Clean up network (optional)
docker network rm global_net
```

### Running Individual Components

```bash
# User's home only (for testing sensors/gateway)
cd user
docker-compose up --build

# Specific user instance with custom name
docker-compose -f user/docker-compose.yml --project-name user2 up --build
```

### Development and Testing

```bash
# Install Python dependencies for local testing
pip install -r sensor_temperature/requirements.txt

# Test temperature simulator locally
python sensor_temperature/timeseries_get.py

# View Kafka topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Consume Kafka messages
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sensor-raw-data \
  --from-beginning

# Check container logs
docker logs gateway
docker logs cloud-ingestor
docker logs pipeline-p1

# Access InfluxDB UI
# Open browser: http://localhost:8086
# Credentials: admin / adminpassword
```

### Environment Variables

**Sensors (user/docker-compose.yml):**
- `MQTT_HOST`: Hostname of local MQTT broker (mosquitto)
- `SENSOR_TOPIC_DATA`: Topic for publishing temperature readings (e.g., room1/temperature)
- `SENSOR_TOPIC_STATUS`: Topic for receiving heatpump control commands (e.g., room1/heatpump)

**Gateway (user/docker-compose.yml):**
- `MQTT_HOST`: Local MQTT broker hostname (mosquitto)
- `CLOUD_MQTT_HOST`: Cloud MQTT broker hostname (cloud-mosquitto)
- `CLOUD_MQTT_PORT`: Cloud MQTT port (1883)
- `USER_ID`: User identifier (user1)

**Cloud Ingestor (cloud/docker-compose.yml):**
- `MQTT_HOST`: Cloud MQTT broker (cloud-mosquitto)
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka connection (kafka:29092)
- `KAFKA_TOPIC`: Topic to publish to (sensor-raw-data)

**Pipeline P1 (cloud/docker-compose.yml):**
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka connection (kafka:29092)
- `KAFKA_TOPIC`: Topic to consume from (sensor-raw-data)
- `KAFKA_GROUP_ID`: Consumer group ID (pipeline-p1-group)
- `INFLUXDB_URL`: InfluxDB connection (http://influxdb:8086)
- `INFLUXDB_TOKEN`: Authentication token
- `INFLUXDB_ORG`: Organization name (iot-org)
- `INFLUXDB_BUCKET`: Database bucket (iot-bucket)

## Key Implementation Details

### Temperature Simulation Logic (timeseries_get.py:14-39)

- Base temperature varies by season (8°C winter, 30°C summer)
- Daily temperature cycles based on hour of day
- Heatpump on: room_temp increases toward target (capped at 35°C)
- Heatpump off: room_temp decreases (floored at 10°C)
- Physics: temperature changes by base_temp/60 per second (due to 1:60 time ratio)

### Controller Pattern (controller.py)

- Uses paho-mqtt client with async loop (`loop_start()`)
- Global state for heatpump_status controlled via MQTT callback
- Publishes temperature readings every 1 second real time
- Message callback updates heatpump status from JSON payload

### Gateway Implementation (mqtt_getway/gateway.py)

- Dual MQTT client pattern: one for local broker, one for cloud broker
- Subscribes to all topics (#) on local MQTT
- Forwards messages to cloud with user_id prefix: `user_id/original_topic`
- Bridges `internal_net` (user's home) to `global_net` (cloud)

### Cloud Ingestor (cloud/ingestor/ingestor.py)

- MQTT to Kafka bridge
- Enriches messages with metadata extracted from topic path (user_id/room/type)
- Kafka producer with `acks='all'` for reliability
- Validates JSON format before publishing to Kafka

### Pipeline P1 - Save Raw Data (cloud/pipeline-p1/pipeline_p1.py)

- Kafka consumer reading from `sensor-raw-data` topic
- Writes to InfluxDB using proper time-series data model:
  - **Measurement**: `temperature_raw`
  - **Tags**: `user_id`, `room` (indexed for fast queries)
  - **Fields**: `temperature` (float value)
  - **Timestamp**: Preserved from sensor (ISO 8601)
- Uses synchronous write API for data consistency

### InfluxDB Data Model

**Why tags vs fields:**
- Tags (user_id, room) are indexed → enables fast filtering and grouping
- Fields (temperature) are values → optimized for aggregation functions
- Proper use of tags/fields is critical for InfluxDB query performance

**Example query:**
```flux
from(bucket: "iot-bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "temperature_raw")
  |> filter(fn: (r) => r.user_id == "user1")
  |> filter(fn: (r) => r.room == "room1")
```

### Time Simulation

All simulators implement a time acceleration pattern:
```python
sim_diff = current_date.timestamp() - self.start_time.timestamp()
sim_time = datetime.fromtimestamp(self.start_time.timestamp() + (sim_diff * 60))
```
This means the system simulates 60 minutes for every 1 minute of real time.

## Adding New Components

### Adding New Sensors

1. Add service in `user/docker-compose.yml` following existing room pattern
2. Set unique MQTT topics for data and control
3. Ensure service is on `internal_net` and `depends_on` mosquitto

### Adding New Pipelines (P2, P3, P4)

1. Create new directory in `cloud/` (e.g., `pipeline-p2/`)
2. Implement Python script with Kafka consumer
3. Add service to `cloud/docker-compose.yml`
4. Connect to `global_net` and set Kafka environment variables
5. Consider data flow:
   - **P2 (Clean)**: Filter data, save to `temperature_clean`
   - **P3 (Actuate)**: Read clean data, publish commands to MQTT
   - **P4 (Aggregate)**: Calculate statistics, save to `temperature_aggregated`

### Gateway Bidirectional Communication

The gateway can also receive commands from cloud and forward to local devices:
1. Subscribe to cloud MQTT topics for commands (e.g., `user1/+/heatpump`)
2. Forward to local MQTT topics (e.g., `room1/heatpump`)
3. Required for Pipeline P3 (Actuate) to control heat pumps

## Project Requirements Context

This project implements an IoT platform for a university assignment worth 20 points:

**1st Level [50% = 10 points]:** ✅ IMPLEMENTED
- Sensors follow specification
- Gateway forwards MQTT data to cloud
- Pipeline P1 saves raw data to InfluxDB

**2nd Level [25% = 5 points]:** Not yet implemented
- Pipeline P2: Clean data (filter 100°C outliers)
- Pipeline P3: Actuate heat pumps based on temperature
- Pipeline P4: Aggregate data (calculate mean per user)

**3rd Level [25% = 5 points]:** Not yet implemented
- Handle backpressure in actuate pipeline
- Deploy to Kubernetes (Minikube)

## Important Notes for Development

### DO NOT Modify Sensors
The sensor implementation in `sensor_temperature/` is provided and must not be modified per project requirements. All development should focus on gateway and cloud pipelines.

### Kafka Topic Strategy
- `sensor-raw-data`: Raw sensor data from ingestor
- (Future) `sensor-clean-data`: Filtered data from P2
- (Future) `sensor-actuate`: Commands for P3
- Multiple pipelines can consume same Kafka topic independently

### InfluxDB Measurements
- `temperature_raw`: Unfiltered data (P1)
- `temperature_clean`: Filtered data (P2)
- `temperature_aggregated`: Mean values (P4)

### Common Issues

**Gateway won't start:** Ensure `global_net` exists and cloud services are running first

**No data in InfluxDB:** Check each component in sequence:
1. Sensors publishing? Check logs: `docker logs user-room1-1`
2. Gateway forwarding? Check logs: `docker logs gateway`
3. Ingestor receiving? Check logs: `docker logs cloud-ingestor`
4. Kafka has data? Run: `docker exec -it kafka kafka-console-consumer --topic sensor-raw-data --bootstrap-server localhost:9092 --from-beginning`
5. Pipeline P1 writing? Check logs: `docker logs pipeline-p1`

**Port conflicts:** User's local MQTT (1883) vs Cloud MQTT (1884) are intentionally different to avoid conflicts

### Network Architecture Details

The `global_net` must be created externally because:
- It's shared between user's home (gateway) and cloud infrastructure
- Multiple users could connect their gateways to the same cloud
- Simulates real-world scenario where cloud is separate from edge devices

## See Also

- `SETUP_GUIDE.md`: Comprehensive setup and verification instructions
- `IMPLEMENTATION_SUMMARY.md`: Design decisions and architecture details
- `cloud/README.md`: Cloud infrastructure reference
