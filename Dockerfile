FROM python:3.9-slim

RUN addgroup --gid 1001 --system crypto && \
    adduser --shell /bin/false --disabled-password --uid 1001 --system --group tgtg
RUN mkdir -p /app
RUN chown crypto:crypto /app

WORKDIR /app
USER crypto

COPY --chown=crypto:crypto requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

COPY --chown=crypto:crypto ./src .

CMD [ "python", "-u", "runner.py" ]
