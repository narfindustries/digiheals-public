FROM python:3.13-rc-bookworm

RUN mkdir /flask

WORKDIR /flask

COPY app.py requirements.txt ./

RUN pip install -r requirements.txt

ENTRYPOINT flask run --host=0.0.0.0
