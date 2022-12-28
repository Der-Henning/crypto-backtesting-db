FROM python:3.9 AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev

COPY requirements.txt /tmp/pip-tmp/
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r /tmp/pip-tmp/requirements.txt

FROM python:3.9-slim

RUN addgroup --gid 1001 --system crypto && \
    adduser --shell /bin/false --disabled-password --uid 1001 --system --group crypto
RUN mkdir -p /app
RUN chown crypto:crypto /app

USER crypto

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

COPY --chown=crypto:crypto ./src .

CMD [ "python", "-u", "runner.py" ]
