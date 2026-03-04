# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY ./src /app/src
COPY .env.example /app/.env.example

# Expose the port the app runs on (matching docker-compose)
EXPOSE 8004

# Define the command to run the application
# We run main.py directly using uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"]