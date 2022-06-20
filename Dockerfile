FROM python:alpine3.16

RUN apk add --update gcc libc-dev libffi-dev

WORKDIR /app

ENV PIP_ROOT_USER_ACTION=ignore

COPY requirements.txt /app
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD python api.py
