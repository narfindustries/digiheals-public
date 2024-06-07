FROM openjdk:17-jdk
RUN microdnf install maven
COPY java-json-echo-server /java-json-echo-server

WORKDIR /java-json-echo-server

RUN mvn package jetty:effective-web-xml

CMD mvn jetty:run


