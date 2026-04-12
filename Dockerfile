FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gettext \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/ requirements/
RUN pip3 install --no-cache-dir -r requirements/base.txt

COPY . .

RUN chmod +x scripts/entrypoint.sh

ENTRYPOINT ["scripts/entrypoint.sh"]