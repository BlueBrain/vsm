FROM python:3.8

WORKDIR /app
COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt
RUN apt update && apt install telnet httpie vim netcat -y

ADD . /app

RUN pip install --no-cache-dir .

# TODO create a separate worker image?
# TODO add a script to generate  certs ?
#RUN useradd op && chmod 644 /app/certs/* -R
#USER op

ENTRYPOINT ["python3"]
