FROM python:3.8

WORKDIR /app

COPY requirements.txt start_server.py ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY server/ server/
COPY migrations/ migrations/
COPY characters/ characters/

CMD python ./start_server.py

