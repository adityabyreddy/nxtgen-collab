FROM debian:bookworm-slim

ENV PROJECT_WORKDIR=/opt/workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    git \
    ca-certificates \
    jq

COPY gh /bin/

COPY copilot /bin/

COPY run.sh /opt/run.sh

COPY task.json /opt/task.json

RUN chmod +x /opt/run.sh && \
    chmod +x /bin/gh && \
    chmod +x /bin/copilot && \
    mkdir -p $PROJECT_WORKDIR && \
    rm -rf /var/lib/apt/lists/*

WORKDIR $PROJECT_WORKDIR

CMD ["bash", "/opt/run.sh"]