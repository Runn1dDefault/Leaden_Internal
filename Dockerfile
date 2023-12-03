FROM python:3.11

RUN apt-get update

RUN pip install --upgrade pip

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY . .
COPY ./requirements.txt .
RUN pip install -r requirements.txt

RUN chmod +x entrypoint.sh
ENTRYPOINT ["bash","/app/entrypoint.sh"]