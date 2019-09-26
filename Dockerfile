FROM python:3.6

RUN apt-get update && apt-get install -y postgresql-client wget

ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN mkdir /app

COPY config /app/config
COPY api /app/api
COPY gunicorn /app/gunicorn

COPY requirements.txt /app/requirements.txt
COPY manage.py /app/manage.py
COPY start.sh /app/start.sh
COPY start-wait-for-db.sh /app/start-wait-for-db.sh

WORKDIR /app
RUN pip install -r /app/requirements.txt

EXPOSE 8000
CMD ./start.sh
