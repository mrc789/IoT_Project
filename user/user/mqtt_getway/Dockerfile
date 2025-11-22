FROM python:3.10.0-slim
WORKDIR /gateway
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY gateway.py gateway.py
CMD python3 -u gateway.py
