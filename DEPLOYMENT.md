# Smart PDF Toolkit - Deployment Guide

This guide covers how to deploy and test the Smart PDF Toolkit both locally and on AWS.

## Table of Contents
- [Local Deployment](#local-deployment)
- [AWS Deployment](#aws-deployment)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Local Deployment

### Prerequisites
- Python 3.8+ installed
- Docker and Docker Compose (optional but recommended)
- Git

### Method 1: Direct Python Installation

1. **Clone the repository:**
```bash
git clone https://github.com/siva4it/smart-pdf-toolkit.git
cd smart-pdf-toolkit
```

2. **Create virtual environment:**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install -e .
```

4. **Install system dependencies (Linux/Mac):**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng libreoffice wkhtmltopdf poppler-utils

# macOS (with Homebrew)
brew install tesseract libreoffice wkhtmltopdf poppler
```

5. **Run the application:**

**CLI Mode:**
```bash
smart-pdf --help
smart-pdf merge input1.pdf input2.pdf -o merged.pdf
```

**API Server:**
```bash
smart-pdf-api
# Or with custom settings:
uvicorn smart_pdf_toolkit.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**GUI Application:**
```bash
smart-pdf-gui
```

### Method 2: Docker Deployment

1. **Clone and build:**
```bash
git clone https://github.com/siva4it/smart-pdf-toolkit.git
cd smart-pdf-toolkit
```

2. **Using Docker Compose (Recommended):**
```bash
# Create environment file
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f smart-pdf-api
```

3. **Using Docker directly:**
```bash
# Build the image
docker build -t smart-pdf-toolkit .

# Run API server
docker run -d \
  --name smart-pdf-api \
  -p 8000:8000 \
  -v $(pwd)/uploads:/home/app/uploads \
  -v $(pwd)/output:/home/app/output \
  smart-pdf-toolkit

# Run CLI
docker run --rm \
  -v $(pwd)/files:/home/app/files \
  smart-pdf-toolkit:cli merge file1.pdf file2.pdf -o merged.pdf
```

### Local Testing

1. **Test API endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Upload and process a PDF
curl -X POST \
  -F "file=@sample.pdf" \
  -F "operation=extract_text" \
  http://localhost:8000/api/v1/process

# Get processing status
curl http://localhost:8000/api/v1/status/{task_id}
```

2. **Test CLI commands:**
```bash
# Test basic operations
smart-pdf info sample.pdf
smart-pdf extract-text sample.pdf -o output.txt
smart-pdf merge file1.pdf file2.pdf -o merged.pdf
smart-pdf split large.pdf -p 1-5 -o split_pages.pdf
```

3. **Run test suite:**
```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run specific test categories
pytest tests/test_cli.py -v
pytest tests/test_api.py -v
pytest tests/security/ -v
```

## AWS Deployment

### Architecture Options

#### Option 1: ECS with Fargate (Recommended)
- Serverless container deployment
- Auto-scaling capabilities
- Managed infrastructure

#### Option 2: EC2 with Docker
- More control over infrastructure
- Cost-effective for consistent workloads

#### Option 3: Lambda Functions
- Serverless for specific operations
- Pay-per-use model

### ECS Deployment (Recommended)

1. **Prerequisites:**
```bash
# Install AWS CLI
pip install awscli
aws configure

# Install ECS CLI (optional)
curl -Lo ecs-cli https://amazon-ecs-cli.s3.amazonaws.com/ecs-cli-linux-amd64-latest
chmod +x ecs-cli && sudo mv ecs-cli /usr/local/bin/
```

2. **Create deployment files:**
C
reate `aws/ecs-task-definition.json`:
```json
{
  "family": "smart-pdf-toolkit",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::YOUR_ACCOUNT:role/smart-pdf-toolkit-task-role",
  "containerDefinitions": [
    {
      "name": "smart-pdf-api",
      "image": "YOUR_ACCOUNT.dkr.ecr.YOUR_REGION.amazonaws.com/smart-pdf-toolkit:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "SMART_PDF_OUTPUT_DIR",
          "value": "/app/output"
        },
        {
          "name": "SMART_PDF_MAX_FILE_SIZE",
          "value": "104857600"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT:secret:smart-pdf-toolkit/openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/smart-pdf-toolkit",
          "awslogs-region": "YOUR_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "python -c \"import requests; requests.get('http://localhost:8000/health')\" || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

3. **Deploy to AWS:**
```bash
# Build and push Docker image to ECR
aws ecr get-login-password --region YOUR_REGION | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.YOUR_REGION.amazonaws.com

# Tag and push image
docker build -t smart-pdf-toolkit .
docker tag smart-pdf-toolkit:latest YOUR_ACCOUNT.dkr.ecr.YOUR_REGION.amazonaws.com/smart-pdf-toolkit:latest
docker push YOUR_ACCOUNT.dkr.ecr.YOUR_REGION.amazonaws.com/smart-pdf-toolkit:latest

# Create ECS cluster
aws ecs create-cluster --cluster-name smart-pdf-toolkit-cluster

# Register task definition
aws ecs register-task-definition --cli-input-json file://aws/ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster smart-pdf-toolkit-cluster \
  --service-name smart-pdf-api \
  --task-definition smart-pdf-toolkit:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-abcdef],assignPublicIp=ENABLED}"
```

### EC2 Deployment

1. **Launch EC2 instance:**
```bash
# Create security group
aws ec2 create-security-group \
  --group-name smart-pdf-toolkit-sg \
  --description "Security group for Smart PDF Toolkit"

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-name smart-pdf-toolkit-sg \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name smart-pdf-toolkit-sg \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups smart-pdf-toolkit-sg \
  --user-data file://aws/user-data.sh
```

2. **Create user-data script (`aws/user-data.sh`):**
```bash
#!/bin/bash
yum update -y
yum install -y docker git

# Start Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone and deploy
cd /home/ec2-user
git clone https://github.com/siva4it/smart-pdf-toolkit.git
cd smart-pdf-toolkit

# Create environment file
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
POSTGRES_PASSWORD=secure_password_here
EOF

# Start services
docker-compose up -d

# Setup log rotation
cat > /etc/logrotate.d/smart-pdf-toolkit << EOF
/home/ec2-user/smart-pdf-toolkit/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ec2-user ec2-user
}
EOF
```

### Lambda Deployment (for specific functions)

1. **Create Lambda deployment package:**
```bash
# Create deployment directory
mkdir lambda-deployment
cd lambda-deployment

# Install dependencies
pip install -r ../requirements.txt -t .

# Copy source code
cp -r ../smart_pdf_toolkit .

# Create Lambda function
zip -r smart-pdf-toolkit-lambda.zip .
```

2. **Deploy Lambda function:**
```bash
aws lambda create-function \
  --function-name smart-pdf-text-extractor \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler smart_pdf_toolkit.lambda_handlers.text_extraction.handler \
  --zip-file fileb://smart-pdf-toolkit-lambda.zip \
  --timeout 300 \
  --memory-size 1024
```

## AWS Testing

### Load Testing with Artillery

1. **Install Artillery:**
```bash
npm install -g artillery
```

2. **Create load test configuration (`tests/load/artillery-config.yml`):**
```yaml
config:
  target: 'https://your-alb-endpoint.amazonaws.com'
  phases:
    - duration: 60
      arrivalRate: 5
      name: "Warm up"
    - duration: 300
      arrivalRate: 10
      name: "Sustained load"
    - duration: 120
      arrivalRate: 20
      name: "Peak load"
  payload:
    path: "test-files.csv"
    fields:
      - "filename"

scenarios:
  - name: "PDF Processing"
    weight: 70
    flow:
      - post:
          url: "/api/v1/process"
          formData:
            file: "@{{ filename }}"
            operation: "extract_text"
      - think: 5
      - get:
          url: "/api/v1/status/{{ $randomString() }}"
  
  - name: "Health Check"
    weight: 30
    flow:
      - get:
          url: "/health"
```

3. **Run load tests:**
```bash
artillery run tests/load/artillery-config.yml
```

### Monitoring Setup

1. **CloudWatch Alarms:**
```bash
# CPU utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "smart-pdf-toolkit-high-cpu" \
  --alarm-description "High CPU utilization" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# Memory utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "smart-pdf-toolkit-high-memory" \
  --alarm-description "High memory utilization" \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 85 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

2. **Custom metrics:**
```python
# Add to your application code
import boto3

cloudwatch = boto3.client('cloudwatch')

def put_custom_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='SmartPDFToolkit',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
        ]
    )

# Usage in your code
put_custom_metric('PDFProcessed', 1)
put_custom_metric('ProcessingTime', processing_time, 'Seconds')
```

## Testing

### Unit Tests
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=smart_pdf_toolkit --cov-report=html
```

### Integration Tests
```bash
# Test API endpoints
pytest tests/integration/test_api_integration.py -v

# Test CLI commands
pytest tests/integration/test_cli_integration.py -v

# Test file processing
pytest tests/integration/test_file_processing.py -v
```

### Security Tests
```bash
# Run security test suite
pytest tests/security/ -v

# Run specific security tests
pytest tests/security/test_input_validation.py -v
pytest tests/security/test_api_security.py -v
```

### Performance Tests
```bash
# Run performance benchmarks
pytest tests/performance/ -v --benchmark-only

# Generate performance report
pytest tests/performance/ --benchmark-json=benchmark_results.json
```

### End-to-End Tests
```bash
# Test complete workflows
pytest tests/e2e/ -v

# Test with real files
pytest tests/e2e/test_real_world_scenarios.py -v
```

## Monitoring

### Application Metrics
- Request count and response times
- Error rates and types
- File processing metrics
- Resource utilization

### Infrastructure Metrics
- CPU and memory usage
- Network I/O
- Disk usage
- Container health

### Logging
```python
# Structured logging configuration
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/smart-pdf-toolkit.log')
    ]
)
logger = logging.getLogger(__name__)
logger.handlers[0].setFormatter(JSONFormatter())
```

## Troubleshooting

### Common Issues

1. **Memory Issues:**
```bash
# Check memory usage
docker stats
# Increase memory limits in docker-compose.yml or ECS task definition
```

2. **File Processing Errors:**
```bash
# Check file permissions
ls -la uploads/ temp/ output/
# Ensure directories are writable
chmod 755 uploads/ temp/ output/
```

3. **API Connection Issues:**
```bash
# Check if service is running
curl -I http://localhost:8000/health
# Check logs
docker-compose logs smart-pdf-api
```

4. **Database Connection Issues:**
```bash
# Test database connection
docker-compose exec postgres psql -U smart_pdf_user -d smart_pdf_toolkit
# Check connection string in environment variables
```

### Debug Mode

Enable debug mode for detailed logging:
```bash
# Set environment variable
export SMART_PDF_DEBUG=true

# Or in docker-compose.yml
environment:
  - SMART_PDF_DEBUG=true
```

### Health Checks

Implement comprehensive health checks:
```python
@app.get("/health")
async def health_check():
    checks = {
        "api": "healthy",
        "database": await check_database(),
        "storage": check_storage(),
        "dependencies": check_dependencies()
    }
    
    if all(status == "healthy" for status in checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "checks": checks})
```

This deployment guide provides comprehensive instructions for both local development and AWS production deployments, along with testing strategies and monitoring setup.