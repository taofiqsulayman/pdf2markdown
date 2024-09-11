# Base image with Python
FROM python:3.9-slim

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install GPU support libraries
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy the entire app code into the working directory
COPY . /app

# Expose the default port Streamlit runs on
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py"]
