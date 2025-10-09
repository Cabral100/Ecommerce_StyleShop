FROM python:3.11-slim
WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000
CMD ["/app/entrypoint.sh"]
