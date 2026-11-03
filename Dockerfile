FROM python:3.12-slim

WORKDIR /app
ARG APP_VERSION=dev
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 METRICS_PORT=8000 APP_VERSION=${APP_VERSION}
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY streamlit_app ./streamlit_app

# Run as non-root user for container security
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501 8000
CMD ["python", "streamlit_app/launcher.py"]
