FROM python:3.8-alpine

WORKDIR /app

COPY ./src /app

RUN pip install -r requirements.txt

EXPOSE 5010

ENTRYPOINT python sqs_consumer.py
