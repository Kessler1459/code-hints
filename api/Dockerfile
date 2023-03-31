FROM python:3.11-buster

ADD . ./api

WORKDIR /api

RUN pip install -r requirements.txt

CMD ["uvicorn", "--port", "4200", "--host", "0.0.0.0", "api.start:app"]