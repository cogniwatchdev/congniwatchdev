# CogniWatch - AI Agent Network Scanner + Dashboard
# Multi-service deployment with scanner, web UI, and database

FROM python:3.12-slim

LABEL maintainer="CogniWatch Project"
LABEL description="AI agent framework discovery and monitoring system"

# Install system dependencies for network scanning
RUN apt-get update && apt-get install -y \
    nmap \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /cogniwatch

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scanner/ ./scanner/
COPY webui/ ./webui/
COPY database/ ./database/
COPY agents/ ./agents/
COPY config/ ./config/

# Create data directory for database and logs
RUN mkdir -p /cogniwatch/data

# Make main entry points executable
RUN chmod +x /cogniwatch/scanner/network_scanner.py /cogniwatch/webui/server.py

# Note: Running as root to access host-mounted volumes with correct permissions
# For production, consider rootless Podman or fix volume permissions
# USER cogniwatch

# Expose ports
# 9000: Web UI
# 9001: Scanner API (optional)
EXPOSE 9000 9001

# Set environment defaults
ENV COGNIWATCH_HOST=0.0.0.0
ENV COGNIWATCH_PORT=9000
ENV COGNIWATCH_DEBUG=false

# Default command: run web UI
# For scanner-only mode, override with: python /cogniwatch/scanner/network_scanner.py
CMD ["python3", "/cogniwatch/webui/server.py"]
