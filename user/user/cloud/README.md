# Cloud Infrastructure

This directory contains the cloud infrastructure components for the IoT platform.

## Components

1. **Cloud MQTT Broker** - Receives data from user gateways
2. **Kafka + Zookeeper** - Stream processing platform
3. **InfluxDB** - Time series database
4. **Cloud Ingestor** - Bridges MQTT to Kafka
5. **Pipeline P1** - Saves raw data to InfluxDB

## Quick Start

```bash
# Create the global network (only needed once)
docker network create global_net

# Start cloud services
docker-compose up --build
```

## Services and Ports

- Cloud MQTT: `localhost:1884` (external), `cloud-mosquitto:1883` (internal)
- Kafka: `localhost:9092`
- InfluxDB UI: `http://localhost:8086`
  - Username: `admin`
  - Password: `adminpassword`

## Environment Variables

All services are pre-configured in `docker-compose.yml`. Key variables:

### Cloud Ingestor
- `MQTT_HOST`: Cloud MQTT broker hostname
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka connection string
- `KAFKA_TOPIC`: Topic to publish sensor data

### Pipeline P1
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka connection string
- `KAFKA_TOPIC`: Topic to consume from
- `INFLUXDB_URL`: InfluxDB connection URL
- `INFLUXDB_TOKEN`: Authentication token
- `INFLUXDB_ORG`: Organization name
- `INFLUXDB_BUCKET`: Bucket (database) name

## Viewing Data in InfluxDB

1. Open browser: `http://localhost:8086`
2. Login with credentials above
3. Go to "Data Explorer"
4. Query example:

```flux
from(bucket: "iot-bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "temperature_raw")
  |> filter(fn: (r) => r["user_id"] == "user1")
  |> filter(fn: (r) => r["room"] == "room1")
```

## Checking Kafka Messages

```bash
# List all topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Consume messages
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sensor-raw-data \
  --from-beginning
```

## Stopping Services

```bash
docker-compose down

# Remove volumes (deletes all data)
docker-compose down -v
```
