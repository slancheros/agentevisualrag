FROM python:3.11-slim

WORKDIR /app
# Evita prompts interactivos en apt
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1



COPY constraints.txt .
COPY requirements.txt .
COPY requirements-agent.txt .

# Instala dependencias principales
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

# Instala dependencias de agente (LangChain/LangGraph/LLM)
RUN pip install --no-cache-dir -r requirements-agent.txt -c constraints.txt

# Copia el código de la aplicación
COPY . .


EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
