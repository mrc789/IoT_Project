#!/bin/bash

echo "========================================="
echo "IoT Platform - Startup Script"
echo "========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Create global network if it doesn't exist
if ! docker network ls | grep -q "global_net"; then
    echo "Creating global_net network..."
    docker network create global_net
    echo "✅ Network created"
else
    echo "✅ global_net network already exists"
fi

echo ""
echo "========================================="
echo "IMPORTANT: You need to run services in 2 terminals"
echo "========================================="
echo ""
echo "Terminal 1 - Cloud Services:"
echo "  cd cloud && docker-compose up --build"
echo ""
echo "Terminal 2 - User's Home (wait for cloud to start):"
echo "  cd user && docker-compose up --build"
echo ""
echo "========================================="
echo "Verification:"
echo "========================================="
echo ""
echo "1. InfluxDB UI: http://localhost:8086"
echo "   Username: admin"
echo "   Password: adminpassword"
echo ""
echo "2. Check Kafka topics:"
echo "   docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092"
echo ""
echo "3. View Kafka messages:"
echo "   docker exec -it kafka kafka-console-consumer \\"
echo "     --bootstrap-server localhost:9092 \\"
echo "     --topic sensor-raw-data \\"
echo "     --from-beginning"
echo ""
echo "========================================="
echo "To stop:"
echo "========================================="
echo ""
echo "Press Ctrl+C in both terminals, then run:"
echo "  cd cloud && docker-compose down"
echo "  cd user && docker-compose down"
echo ""
echo "See SETUP_GUIDE.md for detailed instructions"
echo ""
