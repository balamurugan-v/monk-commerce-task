# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir setuptools
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/usr/src/app
ENV FLASK_APP=main.py

# Copy the rest of the application's source code from the host to the image
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
