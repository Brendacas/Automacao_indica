# Usa uma imagem oficial do Python como base
FROM python:3.11-slim

# Define a pasta de trabalho dentro do contêiner
WORKDIR /app

# --- 1. Instalar o Java (JDK) ---
# Necessário para o 'tabula-py' (Script SAF)
RUN apt-get update && apt-get install -y default-jdk && rm -rf /var/lib/apt/lists/*

# --- 2. Instalar Bibliotecas Python ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- 3. Instalar o Playwright (Navegadores e Dependências) ---
RUN playwright install-deps
RUN playwright install

# --- 4. Copiar o Resto do seu Código ---
COPY . .

# --- 5. Comando para Rodar (O Render usa a porta 10000) ---
# Diz ao Gunicorn para escutar na porta 10000
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "run:app"]