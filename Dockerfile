from python:3.14

WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt

ADD . /code/

CMD alembic upgrade head && exec python3 main.py
