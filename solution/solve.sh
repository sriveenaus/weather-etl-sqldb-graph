#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -euo pipefail

echo "Current Directory: $(pwd)"
mkdir -p output


echo "--- Starting ETL ---"
# Run scripts directly since we know where they are
python3 weather_data.py --start 2024-01-01 --end 2024-01-10
python3 visualize.py

# Produce the docker-compose.yaml required by instruction.md              
cat > /app/docker-compose.yaml << 'EOF'                                  
services:                                                                  
  etl:                                                                     
    image: python:3.11-slim                                                
    command: bash solve.sh                                           
EOF                                                                     
echo "ETL pipeline complete"  

echo "Task complete. pipeline finished. Keeping container alive for verifier..."
# This is CRITICAL. Without this, the container dies and Harbor fails.
#tail -f /dev/null
echo "ETL pipeline complete"
