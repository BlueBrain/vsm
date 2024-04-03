FROM python:3.11

WORKDIR /app
COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt
RUN apt update && apt install telnet httpie vim netcat-traditional -y

ADD . /app

RUN pip install --no-cache-dir .

ENTRYPOINT ["python3"]
