FROM neo4j:5.19.0-bullseye

USER root

RUN apt-get update && apt-get -y install python3-pip
RUN pip install gdown
# Download and extract Neo4j test data
RUN gdown --id 105J7X5QR55sUJjT3_I43eGB4AQ2Kq7hh -O neo4jTest.tar.xz
RUN ls -lh neo4jTest.tar.xz
RUN mkdir -p /data
RUN tar -xJf neo4jTest.tar.xz -C /data
