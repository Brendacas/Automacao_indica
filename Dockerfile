FROM python:3.11-slim

# Define a pasta de trabalho dentro do contêiner
WORKDIR /app

RUN apt-get update && \
    apt-get install -y default-jdk && \
    rm -rf /var/lib/apt/lists/* && \
    # VVV ESTA É A NOVA LINHA DE CORREÇÃO VVV
    ln -s /usr/lib/jvm/default-java/lib/server/libjvm.so /usr/lib/libjvm.so

# Define a variável de ambiente JAVA_HOME 
ENV JAVA_HOME /usr/lib/jvm/default-java

# --- 2. Instalar Bibliotecas Python ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala as dependências de sistema APENAS para o chromium
RUN playwright install-deps chromium
# Instala APENAS o navegador chromium
RUN playwright install chromium

# --- 4. Copiar o Resto do seu Código ---
COPY . .

# --- 5. Comando para Rodar (O Render usa a porta 10000) ---
# Diz ao Gunicorn para escutar na porta 10000
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "run:app"]