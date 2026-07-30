FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY examples/ examples/
COPY entry.sh .
RUN chmod +x entry.sh
ENTRYPOINT ["./entry.sh"]
