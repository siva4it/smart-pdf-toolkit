#!/bin/bash

# Smart PDF Toolkit AWS Deployment Script
set -e

# Configuration
PROJECT_NAME="smart-pdf-toolkit"
ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Create ECR repository
create_ecr_repository() {
    log_info "Creating ECR repository..."
    
    REPO_NAME="${PROJECT_NAME}"
    
    # Check if repository exists
    if aws ecr describe-repositories --repository-names $REPO_NAME --region $AWS_REGION &> /dev/null; then
        log_warn "ECR repository $REPO_NAME already exists"
    else
        aws ecr create-repository \
            --repository-name $REPO_NAME \
            --region $AWS_REGION \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256
        log_info "ECR repository $REPO_NAME created"
    fi
    
    # Set lifecycle policy
    aws ecr put-lifecycle-policy \
        --repository-name $REPO_NAME \
        --region $AWS_REGION \
        --lifecycle-policy-text '{
            "rules": [
                {
                    "rulePriority": 1,
                    "description": "Keep last 10 images",
                    "selection": {
                        "tagStatus": "tagged",
                        "countType": "imageCountMoreThan",
                        "countNumber": 10
                    },
                    "action": {
                        "type": "expire"
                    }
                }
            ]
        }'
}

# Build and push Docker image
build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    IMAGE_URI="${ECR_URI}/${PROJECT_NAME}:latest"
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Build image
    docker build -t $PROJECT_NAME:latest --target production .
    
    # Tag image
    docker tag $PROJECT_NAME:latest $IMAGE_URI
    
    # Push image
    docker push $IMAGE_URI
    
    log_info "Image pushed to $IMAGE_URI"
    echo "IMAGE_URI=$IMAGE_URI" > .env.deploy
}

# Create secrets
create_secrets() {
    log_info "Creating secrets..."
    
    # OpenAI API Key
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warn "OPENAI_API_KEY not set, skipping secret creation"
    else
        aws secretsmanager create-secret \
            --name "${PROJECT_NAME}-${ENVIRONMENT}-openai-api-key" \
            --description "OpenAI API Key for Smart PDF Toolkit" \
            --secret-string "$OPENAI_API_KEY" \
            --region $AWS_REGION || log_warn "Secret may already exist"
    fi
    
    # Database password
    if [ -z "$DATABASE_PASSWORD" ]; then
        DATABASE_PASSWORD=$(openssl rand -base64 32)
        log_info "Generated random database password"
    fi
    
    aws ssm put-parameter \
        --name "/smart-pdf-toolkit/database/password" \
        --value "$DATABASE_PASSWORD" \
        --type "SecureString" \
        --overwrite \
        --region $AWS_REGION
}

# Deploy CloudFormation stack
deploy_infrastructure() {
    log_info "Deploying infrastructure..."
    
    STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
    
    # Source the image URI
    source .env.deploy
    
    # Deploy stack
    aws cloudformation deploy \
        --template-file aws/cloudformation-template.yaml \
        --stack-name $STACK_NAME \
        --parameter-overrides \
            ProjectName=$PROJECT_NAME \
            Environment=$ENVIRONMENT \
            ContainerImage=$IMAGE_URI \
            OpenAIAPIKey="${OPENAI_API_KEY:-dummy}" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $AWS_REGION
    
    log_info "Infrastructure deployed successfully"
    
    # Get outputs
    ALB_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
        --output text)
    
    log_info "Application URL: $ALB_URL"
    echo "ALB_URL=$ALB_URL" >> .env.deploy
}

# Wait for deployment
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    source .env.deploy
    
    # Wait for ALB to be ready
    for i in {1..30}; do
        if curl -s -o /dev/null -w "%{http_code}" "$ALB_URL/health" | grep -q "200"; then
            log_info "Deployment is ready!"
            return 0
        fi
        log_info "Waiting... ($i/30)"
        sleep 30
    done
    
    log_error "Deployment did not become ready in time"
    return 1
}

# Run tests
run_tests() {
    log_info "Running deployment tests..."
    
    source .env.deploy
    
    # Basic health check
    if curl -s "$ALB_URL/health" | grep -q "healthy"; then
        log_info "Health check passed"
    else
        log_error "Health check failed"
        return 1
    fi
    
    # API test
    if curl -s "$ALB_URL/api/v1/docs" | grep -q "Smart PDF Toolkit"; then
        log_info "API documentation accessible"
    else
        log_error "API documentation not accessible"
        return 1
    fi
    
    log_info "All tests passed"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f .env.deploy
}

# Main deployment function
main() {
    log_info "Starting deployment of Smart PDF Toolkit to AWS"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $AWS_REGION"
    
    check_prerequisites
    create_ecr_repository
    build_and_push_image
    create_secrets
    deploy_infrastructure
    wait_for_deployment
    run_tests
    
    log_info "Deployment completed successfully!"
    log_info "Application is available at: $(cat .env.deploy | grep ALB_URL | cut -d'=' -f2)"
    
    cleanup
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "destroy")
        log_warn "Destroying infrastructure..."
        aws cloudformation delete-stack \
            --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
            --region $AWS_REGION
        log_info "Stack deletion initiated"
        ;;
    "status")
        aws cloudformation describe-stacks \
            --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
            --region $AWS_REGION \
            --query 'Stacks[0].StackStatus' \
            --output text
        ;;
    "logs")
        aws logs tail "/ecs/${PROJECT_NAME}-${ENVIRONMENT}" \
            --region $AWS_REGION \
            --follow
        ;;
    *)
        echo "Usage: $0 {deploy|destroy|status|logs}"
        exit 1
        ;;
esac