FROM ubuntu

WORKDIR /cron

RUN apt-get update \
    && apt-get install -y cron jq curl \
    && rm -rf /var/lib/apt/lists/*

VOLUME ["/etc/cron.d"]

ENTRYPOINT ["cron", "-f"]
