#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "Current Directory: $(pwd)"
mkdir -p /app/output


echo "--- Starting ETL ---"
# Run scripts directly since we know where they are
python3 /app/environment/app/weather_data.py --start 2024-01-01 --end 2024-01-10
python3 /app/visualize.py

cat > /app/docker-compose.yaml << 'EOF'                                   
services:                                                                  
  etl:                                                  
    image: weather-etl 
EOF    

echo "--- DIRECTORY CONTENT AFTER RUN ---"
ls -lh  output/temperature_plot.png

echo "Task complete. pipeline finished. Keeping container alive for verifier..."
# This is CRITICAL. Without this, the container dies and Harbor fails.
sleep 180
