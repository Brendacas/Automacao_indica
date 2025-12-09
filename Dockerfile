FROM python:3.11

WORKDIR /app

# ===== DEPENDÊNCIAS DE SISTEMA =====
RUN apt-get update && apt-get install -y \
    wget gnupg unzip \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libxkbcommon0 libgtk-3-0 libdrm2 libgbm1 libasound2 \
    openjdk-21-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# ===== PYTHON =====
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===== PLAYWRIGHT =====
RUN pip install playwright
RUN playwright install chromium

COPY . .

CMD gunicorn run:app --bind 0.0.0.0:$PORT
