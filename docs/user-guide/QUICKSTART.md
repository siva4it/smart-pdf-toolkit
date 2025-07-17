# Smart PDF Toolkit - Quick Start Guide

Get up and running with Smart PDF Toolkit in minutes!

## 🚀 Quick Local Setup

### 1. Clone and Install
```bash
git clone https://github.com/siva4it/smart-pdf-toolkit.git
cd smart-pdf-toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### 2. Test Installation
```bash
# Run comprehensive test suite
python scripts/local-test.py

# Or test individual components
smart-pdf --help                    # CLI
python -m smart_pdf_toolkit.api.main  # API (http://localhost:8000)
python -m smart_pdf_toolkit.gui.app   # GUI
```

### 3. Basic Usage Examples

**CLI Commands:**
```bash
# Get PDF information
smart-pdf info document.pdf

# Extract text
smart-pdf extract-text document.pdf -o output.txt

# Merge PDFs
smart-pdf merge file1.pdf file2.pdf -o merged.pdf

# Split PDF
smart-pdf split document.pdf -p 1-5 -o pages_1_to_5.pdf
```

**API Usage:**
```bash
# Start API server
python -m smart_pdf_toolkit.api.main

# Test endpoints
curl http://localhost:8000/health
curl -X POST -F "file=@document.pdf" -F "operation=extract_text" \
  http://localhost:8000/api/v1/process
```

## 🐳 Docker Quick Start

### 1. Using Docker Compose (Recommended)
```bash
# Copy environment template
cp .env.example .env
# Edit .env with your settings (especially OPENAI_API_KEY)

# Start all services
docker-compose up -d

# Test
curl http://localhost:8000/health
```

### 2. Using Docker Directly
```bash
# Build image
docker build -t smart-pdf-toolkit .

# Run API server
docker run -d -p 8000:8000 \
  -v $(pwd)/uploads:/home/app/uploads \
  -v $(pwd)/output:/home/app/output \
  smart-pdf-toolkit

# Run CLI
docker run --rm -v $(pwd)/files:/home/app/files \
  smart-pdf-toolkit:cli info /home/app/files/document.pdf
```

## ☁️ AWS Deployment Quick Start

### Prerequisites
- AWS CLI installed and configured
- Docker installed
- Environment variables set:
  ```bash
  export OPENAI_API_KEY="your-openai-key"
  export AWS_REGION="us-east-1"
  ```

### 1. One-Command Deployment
```bash
# Linux/Mac
./aws/deploy.sh

# Windows PowerShell
.\scripts\deploy-windows.ps1
```

### 2. Manual Deployment Steps
```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name smart-pdf-toolkit

# 2. Build and push image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker build -t smart-pdf-toolkit .
docker tag smart-pdf-toolkit:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/smart-pdf-toolkit:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/smart-pdf-toolkit:latest

# 3. Deploy infrastructure
aws cloudformation deploy \
  --template-file aws/cloudformation-template.yaml \
  --stack-name smart-pdf-toolkit-production \
  --parameter-overrides \
    ContainerImage=YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/smart-pdf-toolkit:latest \
    OpenAIAPIKey=$OPENAI_API_KEY \
  --capabilities CAPABILITY_NAMED_IAM
```

### 3. Test AWS Deployment
```bash
# Get ALB URL from CloudFormation outputs
ALB_URL=$(aws cloudformation describe-stacks \
  --stack-name smart-pdf-toolkit-production \
  --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
  --output text)

# Test endpoints
curl $ALB_URL/health
curl $ALB_URL/docs
```

## 🧪 Testing Quick Start

### Run All Tests
```bash
# Comprehensive local testing
python scripts/local-test.py

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Security tests
pytest tests/security/ -v
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## 📊 Monitoring and Logs

### Local Monitoring
```bash
# View API logs
docker-compose logs -f smart-pdf-api

# Monitor resource usage
docker stats
```

### AWS Monitoring
```bash
# View ECS logs
aws logs tail "/ecs/smart-pdf-toolkit-production" --follow

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=smart-pdf-toolkit-service \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

## 🔧 Configuration

### Environment Variables
Key environment variables to configure:

```bash
# API Configuration
SMART_PDF_HOST=0.0.0.0
SMART_PDF_PORT=8000
SMART_PDF_DEBUG=false

# File Processing
SMART_PDF_MAX_FILE_SIZE=104857600  # 100MB
SMART_PDF_OUTPUT_DIR=./output
SMART_PDF_TEMP_DIR=./temp

# AI Services
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Database (Optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/smart_pdf_toolkit

# AWS (for deployment)
AWS_REGION=us-east-1
AWS_S3_BUCKET=smart-pdf-toolkit-storage
```

### Configuration Files
- `.env` - Local environment configuration
- `docker-compose.yml` - Docker services configuration
- `aws/cloudformation-template.yaml` - AWS infrastructure
- `pyproject.toml` - Python package configuration

## 🚨 Troubleshooting

### Common Issues

**1. Import Errors:**
```bash
# Ensure package is installed in development mode
pip install -e .
```

**2. Docker Build Fails:**
```bash
# Check Docker is running
docker --version
# Clean Docker cache
docker system prune -f
```

**3. API Server Won't Start:**
```bash
# Check port availability
netstat -an | grep 8000
# Check logs
docker-compose logs smart-pdf-api
```

**4. AWS Deployment Fails:**
```bash
# Check AWS credentials
aws sts get-caller-identity
# Validate CloudFormation template
aws cloudformation validate-template --template-body file://aws/cloudformation-template.yaml
```

**5. Tests Failing:**
```bash
# Install test dependencies
pip install -e ".[dev]"
# Check test fixtures exist
ls tests/fixtures/
```

### Getting Help

1. **Check logs:** Always check application logs first
2. **Run diagnostics:** Use `python scripts/local-test.py` for comprehensive testing
3. **Review documentation:** See `DEPLOYMENT.md` and `TESTING.md` for detailed guides
4. **Check issues:** Visit the GitHub repository issues page

## 📚 Next Steps

1. **Customize Configuration:** Edit `.env` file for your specific needs
2. **Add Custom Plugins:** Extend functionality with custom plugins
3. **Set Up Monitoring:** Configure CloudWatch alarms and dashboards
4. **Scale Deployment:** Adjust ECS service desired count and auto-scaling
5. **Security Hardening:** Review and implement additional security measures

## 🎯 Key Features to Try

- **PDF Text Extraction:** Extract text with OCR support
- **Document Merging:** Combine multiple PDFs
- **Format Conversion:** Convert between PDF, DOCX, HTML
- **AI-Powered Analysis:** Summarize and analyze documents
- **Batch Processing:** Process multiple files simultaneously
- **API Integration:** RESTful API for programmatic access
- **GUI Application:** User-friendly desktop interface

Happy processing! 🎉