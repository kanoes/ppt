FROM python:3.11-slim

ENV PYTHONPYCACHEPREFIX=/usr/src/pycache \
    PYTHONPATH=/app \
    TZ=Asia/Tokyo \
    NODE_VERSION=18.x

WORKDIR /app

# Install system dependencies including Node.js
RUN apt update && \
    apt install -y \
        libxmlsec1-dev \
        libxmlsec1-openssl \
        tzdata \
        curl \
        gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION} | bash - && \
    apt install -y nodejs && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install html2pptx globally
COPY refactor_ideas/pptx/html2pptx.tgz ./html2pptx.tgz
RUN npm install -g ./html2pptx.tgz && \
    rm html2pptx.tgz

# Copy application code
COPY src ./src
COPY app.py ./

# Create output and workspace directories
RUN mkdir -p output workspace

EXPOSE 5056

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--bind=0.0.0.0:5056", "--timeout", "0"]
