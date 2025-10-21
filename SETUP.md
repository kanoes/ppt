# Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 16+
- npm

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies

The html2pptx library must be installed globally:

```bash
# Install html2pptx from the included package
npm install -g ./refactor_ideas/pptx/html2pptx.tgz

# Verify installation
npm list -g @ant/html2pptx
```

If the installation fails, ensure the tarball exists:

```bash
ls -lh refactor_ideas/pptx/html2pptx.tgz
```

### 3. Configure Environment

Create `.env` file in project root:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here

# LLM Settings
DEFAULT_LLM_DEPLOYMENT=gpt-5
DEFAULT_LLM_TEMPERATURE=1
```

### 4. Create Output Directory

```bash
mkdir -p output workspace
```

### 5. Test the Setup

```bash
# Start the server
uvicorn app:app --reload --port 5056

# In another terminal, test the endpoint
curl -X POST http://localhost:5056/generate \
  -H "Content-Type: application/json" \
  -d '{
    "userName": "Test User",
    "threadId": "test-123",
    "conversation": [
      {
        "question": {"content": "Test Question"},
        "answer": {"content": "Test Answer"}
      }
    ]
  }'
```

## Troubleshooting

### html2pptx Module Not Found

If you see "Cannot find module '@ant/html2pptx'":

1. Verify global installation:
   ```bash
   npm list -g @ant/html2pptx
   ```

2. Check NODE_PATH is set correctly:
   ```bash
   echo $NODE_PATH
   npm root -g
   ```

3. Reinstall:
   ```bash
   npm uninstall -g @ant/html2pptx
   npm install -g ./refactor_ideas/pptx/html2pptx.tgz
   ```

### Python Import Errors

Ensure you're in the correct directory and PYTHONPATH includes project root:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Docker Setup

Build and run with Docker:

```bash
# Build image
docker build -t ppt-automate .

# Run container
docker run -p 5056:5056 --env-file .env ppt-automate
```

Note: Docker image must include Node.js and npm. Update Dockerfile if needed:

```dockerfile
FROM python:3.11-slim

# Install Node.js
RUN apt update && \
    apt install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Rest of Dockerfile...
```

## Development Mode

For development with auto-reload:

```bash
uvicorn app:app --reload --port 5056 --log-level debug
```

## Production Deployment

Using gunicorn:

```bash
gunicorn -k uvicorn.workers.UvicornWorker app:app \
  --bind=0.0.0.0:5056 \
  --timeout 0 \
  --workers 2
```

## Verification Checklist

- [ ] Python dependencies installed
- [ ] Node.js and npm available
- [ ] html2pptx installed globally
- [ ] .env file configured
- [ ] output/ and workspace/ directories created
- [ ] Server starts without errors
- [ ] Test API call succeeds
- [ ] PPTX file generated in output/

