FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
COPY requirements-agent.txt .

# Instala dependencias principales
RUN pip install --no-cache-dir -r requirements.txt

# Instala dependencias de agente (LangChain/LangGraph/LLM)
RUN pip install --no-cache-dir -r requirements-agent.txt

# Copia el código de la aplicación
COPY . .


EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
