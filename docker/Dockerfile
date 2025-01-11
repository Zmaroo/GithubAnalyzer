FROM node:18-bullseye

# Install Python and system dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create n8n user and set up directories
RUN useradd -ms /bin/bash n8n
RUN mkdir -p /home/n8n/.n8n
RUN chown -R n8n:n8n /home/n8n

# Install n8n globally
RUN npm install -g n8n

# Set up Python environment
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .
RUN chown -R n8n:n8n /app

# Switch to n8n user
USER n8n

# Expose n8n port
EXPOSE 5678

# Start n8n
CMD ["n8n", "start"]
