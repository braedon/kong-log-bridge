FROM python:3.8-slim

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y git \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
	&& pip install --no-cache-dir -r requirements.txt

COPY *.py /app/
COPY utils/*.py /app/utils/
COPY kong_log_bridge/*.py /app/kong_log_bridge/
COPY README.md /app/

EXPOSE 8080

ENTRYPOINT ["python", "-u", "main.py"]
