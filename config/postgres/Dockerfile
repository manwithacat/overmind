FROM postgres:16

# Install build dependencies for Apache AGE
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    wget \
    postgresql-server-dev-16 \
    && rm -rf /var/lib/apt/lists/*

# Download and install Apache AGE 1.5.0
RUN wget -q https://github.com/apache/age/releases/download/PG16/v1.5.0-rc0/apache-age-1.5.0-src.tar.gz \
    && tar xzf apache-age-1.5.0-src.tar.gz \
    && cd apache-age-1.5.0 \
    && make install \
    && cd .. \
    && rm -rf apache-age-1.5.0 apache-age-1.5.0-src.tar.gz

# Clean up build dependencies
RUN apt-get purge -y --auto-remove \
    build-essential \
    ca-certificates \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    wget \
    postgresql-server-dev-16
