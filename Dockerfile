FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

ARG INSTALL_OCR=false
RUN if [ "$INSTALL_OCR" = "true" ]; then \
    sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && \
    apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-spa ca-certificates \
    && rm -rf /var/lib/apt/lists/*; \
  fi

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

CMD ["python", "-m", "processor.main", "worker"]
