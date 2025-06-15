# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 for the FastAPI application
EXPOSE 8000

# Command to run the Uvicorn server, waiting for the DB to be ready
# We'll use a simple sleep here. For production, consider wait-for-it.sh or similar.
CMD ["sh", "-c", "python -c 'import time; time.sleep(15)' && uvicorn main:api_app --host 0.0.0.0 --port 8000"]
