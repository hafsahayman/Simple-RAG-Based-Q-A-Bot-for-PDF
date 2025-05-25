FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=tru
COPY .env /app/.env
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]