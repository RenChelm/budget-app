# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies for Kivy and OpenGL
RUN apt-get update && apt-get install -y \
    python3-dev \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev \
    libgstreamer1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    libgl1-mesa-dev \
    libgles2-mesa-dev \
    libmtdev-dev \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir kivy==2.3.1

# Environment variable to ensure the GUI can find the display
ENV DISPLAY=:0

# Command to run the application
CMD ["python", "main.py"]
