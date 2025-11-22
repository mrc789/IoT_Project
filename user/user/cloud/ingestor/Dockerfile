FROM python:3.10.0-slim
WORKDIR /ingestor
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY ingestor.py ingestor.py
CMD python3 -u ingestor.py
