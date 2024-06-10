FROM alpine:3.19

RUN apk add openjdk17 git python3 py3-pip

RUN git clone https://github.com/synthetichealth/synthea

WORKDIR /synthea

RUN python3 -m venv /venv 
ENV PATH="/venv/bin:$PATH"
RUN pip install flask

RUN ./gradlew run

COPY server.py .
ADD fuzzer ./fuzzer

COPY synthea.properties /synthea/src/main/resources/synthea.properties

EXPOSE 9000

WORKDIR /tmp
RUN git clone https://github.com/mseclab/PyJFuzz && cd PyJFuzz && git checkout 578d44c && python setup.py install && cd .. && rm -r PyJFuzz

COPY snodge /opt/snodge

WORKDIR /opt/snodge

RUN apk add nodejs npm && npm install



WORKDIR /synthea
ENV PYTHONUNBUFFERED 1
CMD ["flask", "--app", "server", "run", "-p", "9000", "-h", "0.0.0.0"]

