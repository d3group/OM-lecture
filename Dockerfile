FROM python:3.11-slim

# Set workdir inside apps
WORKDIR /app/apps

# Copy requirements
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy apps folder
COPY apps/ .



