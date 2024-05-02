FROM alpine:3.19

RUN apk add py3-pip python3

COPY . /fhir-tools

WORKDIR /fhir-tools/

RUN pip install -r requirements.txt --break-system-packages

CMD ["sleep", "infinity"]

