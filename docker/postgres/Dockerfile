FROM postgres:16

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential postgresql-server-dev-16 ca-certificates wget \
        zlib1g-dev liblz4-dev libzstd-dev libreadline-dev libssl-dev \
    && wget -qO /tmp/q3c.tar.gz https://github.com/segasai/q3c/archive/refs/tags/v2.0.1.tar.gz \
    && tar -xzf /tmp/q3c.tar.gz -C /tmp \
    && cd /tmp/q3c-2.0.1 \
    && make && make install \
    && cd / && rm -rf /tmp/q3c* \
    && apt-get purge -y build-essential postgresql-server-dev-16 wget \
        zlib1g-dev liblz4-dev libzstd-dev libreadline-dev libssl-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
