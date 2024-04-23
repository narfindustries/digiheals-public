FROM alpine:3.19

RUN apk add openjdk17 git python3 py3-pip

RUN git clone https://github.com/synthetichealth/synthea

WORKDIR /synthea

RUN python3 -m venv /venv 
ENV PATH="/venv/bin:$PATH"
RUN pip install flask

RUN ./gradlew run

COPY server.py .

COPY synthea.properties /synthea/src/main/resources/synthea.properties

EXPOSE 9000

CMD ["flask", "--app", "server", "run", "-p", "9000", "-h", "0.0.0.0"]
