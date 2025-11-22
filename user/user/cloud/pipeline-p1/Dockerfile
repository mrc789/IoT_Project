FROM python:3.10.0-slim
WORKDIR /pipeline
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY pipeline_p1.py pipeline_p1.py
CMD python3 -u pipeline_p1.py
