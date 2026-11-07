FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    wget \
    python3 \
    python3-pip \
    libhwloc-dev \
    libuv1-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install requests

WORKDIR /app

RUN wget https://github.com/xmrig/xmrig/releases/download/v6.21.1/xmrig-6.21.1-linux-static-x64.tar.gz \
    && tar xzf xmrig-6.21.1-linux-static-x64.tar.gz \
    && mv xmrig-6.21.1/xmrig . \
    && chmod +x xmrig \
    && rm -rf xmrig-6.21.1 xmrig-6.21.1-linux-static-x64.tar.gz

COPY config.json .
COPY miner.py .

CMD ["python3", "miner.py"]
