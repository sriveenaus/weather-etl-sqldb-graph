FROM python:3.11-slim-bookworm

WORKDIR /app

# Install git and other dependencies
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Install latest harbor-cli from GitHub (main branch)
RUN pip install --no-cache-dir harbor-cli==0.3.0

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install pandas matplotlib sqlalchemy pyarrow pytest 

# Copy scripts directly into the container
COPY weather_data.py .
COPY visualize.py .
#COPY requirements.txt .
COPY solve.sh . 
RUN chmod +x solve.sh

# Create the output directory inside the container
RUN mkdir -p output

# Optional: test file
RUN echo "Hello, world!" > /app/hello.txt

RUN chmod +x solve.sh

# Default entrypoint (can override in docker-compose run)
ENTRYPOINT ["python3","weather_data.py"]

