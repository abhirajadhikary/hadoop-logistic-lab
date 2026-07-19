FROM eclipse-temurin:8-jdk-jammy

RUN apt-get update && \
    apt-get install -y procps net-tools curl && \
    rm -rf /var/lib/apt/lists/*

ENV PIG_HOME=/opt/pig
ENV HADOOP_CONF_DIR=/etc/hadoop
ENV PATH=$PIG_HOME/bin:$PATH

WORKDIR /workspace

CMD ["tail", "-f", "/dev/null"]