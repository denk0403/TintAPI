# Deploy with 'heroku container:push web'
# Get Ubuntu Doocker Image
FROM ubuntu:latest

# Install all environment dependencies
RUN apt-get update \
    && apt-get -y install python3 \
    && apt-get install python3-venv

WORKDIR /app
COPY . /app

# Create a virtual environment
RUN python3 -m venv env

# Activate virtual environment
RUN source env/bin/activate

# Install API dependencies
RUN python3 -m pip install -r requirements.txt

# Change directory permissions
RUN chmod -R 777 ./