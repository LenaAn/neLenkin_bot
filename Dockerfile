FROM python:3.14

WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt

ADD . /code/

CMD alembic -c alembic-docker.ini upgrade head && exec python3 main.py

# docker build . -t nelenkin-club/bot:latest
