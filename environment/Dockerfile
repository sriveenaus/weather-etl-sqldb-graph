FROM python:3.11-slim

WORKDIR /app
# 1. Install system dependencies (dos2unix) and Python libs
RUN apt-get update && apt-get install -y dos2unix && rm -rf /var/lib/apt/lists/*
RUN pip install pandas==2.2.2
RUN pip install requests==2.32.3 click==8.1.7 pyarrow==17.0.0 
RUN pip install matplotlib==3.9.2

# 2. Create directories and set permissions FIRST
RUN mkdir -p /app/output /logs/verifier && chmod -R 777 /logs /app/output

# 3. Copy everything (only need to do this once)
COPY app/weather_raw.json /app/weather_raw.json 
#COPY app/ /app/
#COPY app/data/weather.csv /app/data/weather.csv
# 4. Fix line endings and permissions - Removing this check below, as harness does this instead of from app
#RUN dos2unix /app/solve.sh && chmod +x /app/solve.sh

# 5. Use ENTRYPOINT with the absolute path
CMD ["bash"]
