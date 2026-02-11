FROM python:3.9-slim-bullseye


RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libaio1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/oracle


ADD https://download.oracle.com/otn_software/linux/instantclient/1925000/instantclient-basic-linux.x64-19.25.0.0.0dbru.zip /opt/oracle/instantclient.zip

RUN unzip instantclient.zip \
    && rm instantclient.zip


ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_19_25:$LD_LIBRARY_PATH
ENV TNS_ADMIN=/opt/oracle/instantclient_19_25/network/admin


WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8888


CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
