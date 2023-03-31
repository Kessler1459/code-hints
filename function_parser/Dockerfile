FROM python:3.11-buster

ADD . ./parser

WORKDIR /parser

RUN pip install -r requirements.txt

CMD ["python", "./main.py"]
