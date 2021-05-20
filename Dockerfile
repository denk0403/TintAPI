# Deploy with 'heroku container:push web'
# Get Ubuntu Doocker Image
FROM ubuntu:latest

# Install all environment dependencies
RUN apt-get update \
    && apt-get -y install python3.9 python3-pip \
    && pip3 install pipenv

WORKDIR /app
COPY . /app

# Install API dependencies
RUN pipenv install

# Change directory permissions
RUN chmod -R 777 ./

# Run command
CMD OPENAPI_URL= pipenv run prod