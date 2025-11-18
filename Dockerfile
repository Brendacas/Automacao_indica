FROM python:3.11

WORKDIR /app

#JAVA
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk-headless wget gnupg libnss3 libxkbcommon0 libgtk-3-0 libdrm2 libgbm1 && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
ENV PATH="$JAVA_HOME/bin:$PATH"

#PLAYWRIGHT
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install playwright
RUN playwright install chromium

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "run:app"]
