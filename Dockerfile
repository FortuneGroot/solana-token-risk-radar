FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home radar && mkdir -p /app/data /app/logs && chown -R radar:radar /app
USER radar
CMD ["python","run.py"]
