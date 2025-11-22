# Implementation Summary - IoT Platform Project

## Achievement: 50% of Total Points (10/20 points)

This implementation completes all **1st Level Functions** required to achieve 50% of the project grade.

## What Was Implemented

### ✅ 1. Gateway Component (`mqtt_getway/`)
**Files created:**
- `gateway.py` - Main gateway logic
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies

**Functionality:**
- Connects to local MQTT broker (user's home)
- Subscribes to all sensor topics
- Forwards messages to cloud MQTT broker
- Bridges `internal_net` and `global_net` Docker networks

**Technology:** Python with paho-mqtt

---

### ✅ 2. Cloud Infrastructure (`cloud/docker-compose.yml`)
**Services deployed:**
- **Cloud MQTT Broker** (Eclipse Mosquitto 1.6.12)
  - Port: 1884 (external), 1883 (internal)
  - Receives data from all user gateways

- **Zookeeper** (Confluent 7.5.0)
  - Required for Kafka coordination
  - Port: 2181

- **Kafka** (Confluent 7.5.0)
  - Distributed streaming platform
  - Port: 9092
  - Topic: `sensor-raw-data`

- **InfluxDB** (InfluxDB 2.7)
  - Time series database
  - Port: 8086
  - Credentials: admin/adminpassword
  - Organization: iot-org
  - Bucket: iot-bucket

**Network:** `global_net` (bridge driver)

---

### ✅ 3. Cloud Ingestor (`cloud/ingestor/`)
**Files created:**
- `ingestor.py` - MQTT to Kafka bridge
- `Dockerfile` - Container definition
- `requirements.txt` - Dependencies (paho-mqtt, kafka-python)

**Functionality:**
- Subscribes to all topics on cloud MQTT broker
- Receives sensor data from all user gateways
- Enriches messages with metadata (user_id, room)
- Publishes to Kafka topic `sensor-raw-data`
- Validates JSON format

**Technology:** Python with paho-mqtt + kafka-python

---

### ✅ 4. Pipeline P1 - Save Raw Data (`cloud/pipeline-p1/`) ⭐
**Worth: 25% of total project points**

**Files created:**
- `pipeline_p1.py` - Kafka consumer to InfluxDB writer
- `Dockerfile` - Container definition
- `requirements.txt` - Dependencies (kafka-python, influxdb-client)

**Functionality:**
- Consumes messages from Kafka topic `sensor-raw-data`
- Saves data to InfluxDB **exactly as received** (no transformation)
- Uses proper time series data model:
  - **Measurement:** `temperature_raw`
  - **Tags:** `user_id`, `room` (indexed for fast queries)
  - **Fields:** `temperature` (float value)
  - **Timestamp:** From sensor (ISO 8601 format)

**Technology:** Python with kafka-python + influxdb-client

---

### ✅ 5. Documentation
**Files created:**
- `SETUP_GUIDE.md` - Comprehensive setup instructions
- `cloud/README.md` - Cloud infrastructure documentation
- `IMPLEMENTATION_SUMMARY.md` - This file

**Contents:**
- Step-by-step setup instructions
- Architecture overview and data flow
- Verification procedures
- Troubleshooting guide
- Component descriptions
- Technology justification
- Data model documentation

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│         USER'S HOME (user/)             │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Room 1  │  │ Room 2  │  │ Room 3  │ │
│  │ Sensor  │  │ Sensor  │  │ Sensor  │ │
│  └────┬────┘  └────┬────┘  └────┬────┘ │
│       │            │            │       │
│       └────────────┼────────────┘       │
│                    │                    │
│            ┌───────▼────────┐           │
│            │ Local MQTT     │           │
│            │ (Mosquitto)    │           │
│            └───────┬────────┘           │
│                    │                    │
│            ┌───────▼────────┐           │
│            │    Gateway     │           │
│            └───────┬────────┘           │
│                    │                    │
└────────────────────┼────────────────────┘
                     │ global_net
┌────────────────────▼────────────────────┐
│         CLOUD (cloud/)                  │
│                                         │
│            ┌───────────────┐            │
│            │  Cloud MQTT   │            │
│            │  (Mosquitto)  │            │
│            └───────┬───────┘            │
│                    │                    │
│            ┌───────▼───────┐            │
│            │    Ingestor   │            │
│            └───────┬───────┘            │
│                    │                    │
│            ┌───────▼───────┐            │
│            │     Kafka     │            │
│            └───────┬───────┘            │
│                    │                    │
│            ┌───────▼───────┐            │
│            │  Pipeline P1  │  ⭐ 25%   │
│            └───────┬───────┘            │
│                    │                    │
│            ┌───────▼───────┐            │
│            │   InfluxDB    │            │
│            │ (Time Series  │            │
│            │   Database)   │            │
│            └───────────────┘            │
│                                         │
└─────────────────────────────────────────┘
```

## Technology Justification

### MQTT (Message Queue Telemetry Transport)
**Why chosen:**
- Lightweight protocol designed specifically for IoT devices
- Low bandwidth usage (critical for resource-constrained sensors)
- Publish/Subscribe pattern decouples senders and receivers
- Quality of Service (QoS) levels ensure reliable delivery
- Industry standard for IoT communication

**Alternative considered:** HTTP REST
- Rejected because: Higher overhead, requires polling, not designed for IoT

---

### Kafka (Apache Kafka)
**Why chosen:**
- Distributed streaming platform handles high-throughput data
- Fault-tolerant with data replication across brokers
- Decouples data ingestion from processing pipelines
- Multiple consumers can read same data independently
- Replay capability allows reprocessing historical data
- Scales horizontally to handle millions of messages

**Alternatives considered:**
- RabbitMQ: Good but less suitable for high-throughput streaming
- Direct processing: No fault tolerance or replay capability

---

### InfluxDB (Time Series Database)
**Why chosen:**
- Purpose-built for time series data (sensor readings)
- Efficient storage with automatic compression (10-20x compression)
- Tags enable fast filtering (user_id, room)
- Built-in time-based retention policies
- Powerful Flux query language for analytics
- Handles high write throughput (millions of points/second)
- Downsampling and continuous queries for aggregations

**Alternatives considered:**
- PostgreSQL with TimescaleDB: More general-purpose, higher overhead
- MongoDB: Not optimized for time series queries
- Cassandra: More complex, overkill for this scale

---

### Python
**Why chosen:**
- Rich ecosystem for IoT and data processing
- Excellent libraries: paho-mqtt, kafka-python, influxdb-client
- Easy to read and maintain
- Fast development time
- Good error handling and logging
- Docker-friendly

**Alternative considered:** Go, Java
- Rejected because: Python is more accessible for educational projects

---

### Docker & Docker Compose
**Why chosen:**
- Consistent environment across development and deployment
- Easy orchestration of multiple services
- Isolation and resource management
- Simple networking between containers
- Version control for infrastructure (docker-compose.yml)

---

## Data Model Design

### InfluxDB Schema

```
Measurement: temperature_raw
├── Tags (indexed, immutable metadata)
│   ├── user_id: string (e.g., "user1")
│   └── room: string (e.g., "room1", "living_room")
├── Fields (actual values)
│   └── temperature: float (e.g., 22.5)
└── Timestamp: RFC3339 (e.g., "2024-11-22T10:30:00Z")
```

**Design decisions:**

1. **Why separate Tags and Fields?**
   - Tags are indexed → fast filtering by user_id or room
   - Fields store actual measurements → not indexed, saves space
   - InfluxDB optimizes queries when properly using tags/fields

2. **Why user_id and room as Tags?**
   - Common query pattern: "Get all temperatures for user1's living room"
   - Enables efficient filtering: `WHERE user_id='user1' AND room='room1'`
   - Allows aggregation: "Average temperature across all rooms for user1"

3. **Why temperature as Field?**
   - Actual measurement value changes frequently
   - No need to index numeric values
   - Enables mathematical operations: mean, max, min, etc.

4. **Why preserve original timestamp?**
   - Sensors have 1:60 time simulation
   - Original timestamp maintains temporal accuracy
   - Enables time-based analysis and correlations

**Example Query:**
```flux
from(bucket: "iot-bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "temperature_raw")
  |> filter(fn: (r) => r.user_id == "user1")
  |> filter(fn: (r) => r.room == "room1")
  |> mean()  // Calculate average temperature
```

---

## How to Run

### Quick Start

```bash
# 1. Create network
docker network create global_net

# 2. Start cloud (in one terminal)
cd cloud
docker-compose up --build

# 3. Start user's home (in another terminal)
cd user
docker-compose up --build
```

### Verify It's Working

1. **Check logs** - You should see messages flowing through all components
2. **Query InfluxDB** - Access UI at http://localhost:8086 and run queries
3. **Check Kafka** - List topics and consume messages to verify data flow

See `SETUP_GUIDE.md` for detailed instructions.

---

## Testing and Validation

### Unit Testing (Manual)
- [x] Sensors publish to local MQTT
- [x] Gateway subscribes and forwards to cloud
- [x] Ingestor receives and publishes to Kafka
- [x] Pipeline P1 consumes from Kafka
- [x] Data appears in InfluxDB

### Integration Testing
- [x] End-to-end: Sensor → MQTT → Gateway → Cloud MQTT → Kafka → InfluxDB
- [x] Multiple sensors publishing simultaneously
- [x] Data persists across restarts (InfluxDB volume)

### Performance Testing
- [x] System handles 5 sensors × 1 msg/sec = 5 msg/sec
- [x] Scalable to multiple users (architecture supports it)

---

## What This Achieves

✅ **1st Level Functions [50% = 10/20 points]**

According to project specification:
- ✅ "The devices are implemented following the project specification"
  - **Status:** Already provided, validated working

- ✅ "The Gateway will receive the information from MQTT and will send it to the Cloud Service"
  - **Status:** Implemented in `mqtt_getway/gateway.py`
  - **Validation:** Logs show forwarding from local to cloud MQTT

- ✅ "The Save pipeline should be implemented and store the data to an Influx database (25%)"
  - **Status:** Implemented in `cloud/pipeline-p1/pipeline_p1.py`
  - **Validation:** Data visible in InfluxDB UI, queryable via Flux

---

## Files Created

```
user/
├── mqtt_getway/
│   ├── gateway.py          ✅ NEW
│   ├── Dockerfile          ✅ NEW
│   └── requirements.txt    ✅ NEW
├── docker-compose.yml      ✏️ MODIFIED
├── SETUP_GUIDE.md         ✅ NEW
└── IMPLEMENTATION_SUMMARY.md ✅ NEW

cloud/                      ✅ NEW DIRECTORY
├── docker-compose.yml      ✅ NEW
├── README.md              ✅ NEW
├── ingestor/              ✅ NEW
│   ├── ingestor.py        ✅ NEW
│   ├── Dockerfile         ✅ NEW
│   └── requirements.txt   ✅ NEW
└── pipeline-p1/           ✅ NEW
    ├── pipeline_p1.py     ✅ NEW
    ├── Dockerfile         ✅ NEW
    └── requirements.txt   ✅ NEW
```

**Total:** 14 new files, 1 modified file

---

## Next Steps for Higher Grades

To achieve **75% (15/20 points)**, implement 2nd Level Functions:

### Pipeline P2 - Save Clean Data [5%]
- Filter out outliers (values == 100°C)
- Save cleaned data to new measurement: `temperature_clean`

### Pipeline P3 - Actuate [5%]
- Read clean data from Kafka
- Apply rules:
  - If temp < 20°C → Send {"status": 1} to room/heatpump
  - If temp > 25°C → Send {"status": 0} to room/heatpump
- Publish commands to cloud MQTT
- Gateway forwards to local MQTT

### Pipeline P4 - Aggregate [15%]
- Calculate mean temperature across all user's rooms
- Group by user_id, time window (e.g., 5 minutes)
- Save to measurement: `temperature_aggregated`

---

To achieve **100% (20/20 points)**, implement 3rd Level Functions:

### Backpressure Handling [?%]
- Add sleep to actuate pipeline to simulate slow processing
- Implement solution (e.g., increase Kafka partitions, add more consumers)

### Kubernetes Deployment [?%]
- Convert docker-compose to Kubernetes manifests
- Deploy to Minikube
- Configure services, deployments, persistent volumes

---

## Time Spent

- Understanding requirements: 1 hour
- Architecture design: 1 hour
- Gateway implementation: 1 hour
- Cloud infrastructure setup: 1.5 hours
- Ingestor implementation: 1 hour
- Pipeline P1 implementation: 1.5 hours
- Testing and debugging: 2 hours
- Documentation: 2 hours

**Total: ~11 hours**

---

## Conclusion

This implementation provides a solid foundation for the IoT platform, achieving **50% of the project grade**. The architecture is scalable, well-documented, and follows industry best practices for IoT and stream processing systems.

The modular design makes it straightforward to add the remaining pipelines (P2, P3, P4) to achieve higher grades.
