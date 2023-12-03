FROM python:3.11

RUN apt-get update

RUN pip install --upgrade pip

RUN mkdir /leadgen-celery

WORKDIR /leadgen-celery

COPY . /leadgen-celery

RUN pip install -r requirements.txt
RUN playwright install firefox
RUN playwright install-deps
