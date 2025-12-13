# 1. Usar uma imagem leve do Python
FROM python:3.11-slim

# 2. Configurar variáveis de ambiente para Python não gerar arquivos .pyc e logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Definir pasta de trabalho dentro do container
WORKDIR /app

# 4. Instalar dependências do sistema necessárias para PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 5. Copiar requisitos e instalar dependências Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# 6. Copiar o restante do código do projeto
COPY . /app/

# 7. Coletar arquivos estáticos (CSS/JS)
RUN python manage.py collectstatic --noinput

# 8. Comando para iniciar o servidor (Gunicorn)
# Substitua 'config' pelo nome da pasta onde está o seu settings.py
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:80"]