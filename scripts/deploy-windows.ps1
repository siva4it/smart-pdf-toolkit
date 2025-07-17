# Smart PDF Toolkit Windows Deployment Script
param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$Action = "deploy"
)

# Configuration
$ProjectName = "smart-pdf-toolkit"
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check AWS CLI
    try {
        aws --version | Out-Null
        Write-Info "AWS CLI found"
    }
    catch {
        Write-Error "AWS CLI is not installed or not in PATH"
        exit 1
    }
    
    # Check Docker
    try {
        docker --version | Out-Null
        Write-Info "Docker found"
    }
    catch {
        Write-Error "Docker is not installed or not running"
        exit 1
    }
    
    # Check AWS credentials
    try {
        $accountId = aws sts get-caller-identity --query Account --output text
        Write-Info "AWS Account ID: $accountId"
        return $accountId
    }
    catch {
        Write-Error "AWS credentials not configured"
        exit 1
    }
}

# Create ECR repository
function New-ECRRepository {
    param([string]$AccountId)
    
    Write-Info "Creating ECR repository..."
    
    $repoName = $ProjectName
    
    # Check if repository exists
    try {
        aws ecr describe-repositories --repository-names $repoName --region $Region | Out-Null
        Write-Warn "ECR repository $repoName already exists"
    }
    catch {
        aws ecr create-repository `
            --repository-name $repoName `
            --region $Region `
            --image-scanning-configuration scanOnPush=true `
            --encryption-configuration encryptionType=AES256
        Write-Info "ECR repository $repoName created"
    }
    
    # Set lifecycle policy
    $lifecyclePolicy = @"
{
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
}
"@
    
    $lifecyclePolicy | aws ecr put-lifecycle-policy `
        --repository-name $repoName `
        --region $Region `
        --lifecycle-policy-text file://
}

# Build and push Docker image
function Publish-DockerImage {
    param([string]$AccountId)
    
    Write-Info "Building and pushing Docker image..."
    
    $ecrUri = "$AccountId.dkr.ecr.$Region.amazonaws.com"
    $imageUri = "$ecrUri/$ProjectName`:latest"
    
    # Login to ECR
    aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ecrUri
    
    # Build image
    docker build -t "$ProjectName`:latest" --target production .
    
    # Tag image
    docker tag "$ProjectName`:latest" $imageUri
    
    # Push image
    docker push $imageUri
    
    Write-Info "Image pushed to $imageUri"
    
    # Save image URI for later use
    Set-Content -Path ".env.deploy" -Value "IMAGE_URI=$imageUri"
    
    return $imageUri
}

# Create secrets
function New-Secrets {
    Write-Info "Creating secrets..."
    
    # OpenAI API Key
    $openaiKey = $env:OPENAI_API_KEY
    if ($openaiKey) {
        try {
            aws secretsmanager create-secret `
                --name "$ProjectName-$Environment-openai-api-key" `
                --description "OpenAI API Key for Smart PDF Toolkit" `
                --secret-string $openaiKey `
                --region $Region
        }
        catch {
            Write-Warn "OpenAI API Key secret may already exist"
        }
    }
    else {
        Write-Warn "OPENAI_API_KEY environment variable not set"
    }
    
    # Database password
    $dbPassword = $env:DATABASE_PASSWORD
    if (-not $dbPassword) {
        # Generate random password
        $dbPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})
        Write-Info "Generated random database password"
    }
    
    aws ssm put-parameter `
        --name "/smart-pdf-toolkit/database/password" `
        --value $dbPassword `
        --type "SecureString" `
        --overwrite `
        --region $Region
}

# Deploy infrastructure
function Deploy-Infrastructure {
    param([string]$ImageUri)
    
    Write-Info "Deploying infrastructure..."
    
    $stackName = "$ProjectName-$Environment"
    
    $openaiKey = $env:OPENAI_API_KEY
    if (-not $openaiKey) {
        $openaiKey = "dummy"
    }
    
    aws cloudformation deploy `
        --template-file aws/cloudformation-template.yaml `
        --stack-name $stackName `
        --parameter-overrides `
            ProjectName=$ProjectName `
            Environment=$Environment `
            ContainerImage=$ImageUri `
            OpenAIAPIKey=$openaiKey `
        --capabilities CAPABILITY_NAMED_IAM `
        --region $Region
    
    Write-Info "Infrastructure deployed successfully"
    
    # Get ALB URL
    $albUrl = aws cloudformation describe-stacks `
        --stack-name $stackName `
        --region $Region `
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' `
        --output text
    
    Write-Info "Application URL: $albUrl"
    Add-Content -Path ".env.deploy" -Value "ALB_URL=$albUrl"
    
    return $albUrl
}

# Wait for deployment
function Wait-ForDeployment {
    param([string]$AlbUrl)
    
    Write-Info "Waiting for deployment to be ready..."
    
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "$AlbUrl/health" -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Info "Deployment is ready!"
                return $true
            }
        }
        catch {
            # Continue waiting
        }
        
        Write-Info "Waiting... ($i/30)"
        Start-Sleep -Seconds 30
    }
    
    Write-Error "Deployment did not become ready in time"
    return $false
}

# Run tests
function Test-Deployment {
    param([string]$AlbUrl)
    
    Write-Info "Running deployment tests..."
    
    # Health check
    try {
        $response = Invoke-WebRequest -Uri "$AlbUrl/health" -UseBasicParsing
        if ($response.Content -like "*healthy*") {
            Write-Info "Health check passed"
        }
        else {
            Write-Error "Health check failed"
            return $false
        }
    }
    catch {
        Write-Error "Health check error: $($_.Exception.Message)"
        return $false
    }
    
    # API docs check
    try {
        $response = Invoke-WebRequest -Uri "$AlbUrl/docs" -UseBasicParsing
        if ($response.Content -like "*Smart PDF Toolkit*") {
            Write-Info "API documentation accessible"
        }
        else {
            Write-Error "API documentation not accessible"
            return $false
        }
    }
    catch {
        Write-Error "API docs error: $($_.Exception.Message)"
        return $false
    }
    
    Write-Info "All tests passed"
    return $true
}

# Destroy infrastructure
function Remove-Infrastructure {
    Write-Warn "Destroying infrastructure..."
    
    $stackName = "$ProjectName-$Environment"
    
    aws cloudformation delete-stack `
        --stack-name $stackName `
        --region $Region
    
    Write-Info "Stack deletion initiated"
}

# Get stack status
function Get-StackStatus {
    $stackName = "$ProjectName-$Environment"
    
    try {
        $status = aws cloudformation describe-stacks `
            --stack-name $stackName `
            --region $Region `
            --query 'Stacks[0].StackStatus' `
            --output text
        
        Write-Info "Stack Status: $status"
    }
    catch {
        Write-Error "Stack not found or error retrieving status"
    }
}

# View logs
function Get-Logs {
    Write-Info "Fetching logs..."
    
    aws logs tail "/ecs/$ProjectName-$Environment" `
        --region $Region `
        --follow
}

# Main deployment function
function Start-Deployment {
    Write-Info "Starting deployment of Smart PDF Toolkit to AWS"
    Write-Info "Environment: $Environment"
    Write-Info "Region: $Region"
    
    $accountId = Test-Prerequisites
    New-ECRRepository -AccountId $accountId
    $imageUri = Publish-DockerImage -AccountId $accountId
    New-Secrets
    $albUrl = Deploy-Infrastructure -ImageUri $imageUri
    
    if (Wait-ForDeployment -AlbUrl $albUrl) {
        if (Test-Deployment -AlbUrl $albUrl) {
            Write-Info "🎉 Deployment completed successfully!"
            Write-Info "Application is available at: $albUrl"
        }
        else {
            Write-Error "Deployment tests failed"
        }
    }
    else {
        Write-Error "Deployment failed to become ready"
    }
    
    # Cleanup
    if (Test-Path ".env.deploy") {
        Remove-Item ".env.deploy"
    }
}

# Main script logic
switch ($Action.ToLower()) {
    "deploy" {
        Start-Deployment
    }
    "destroy" {
        Remove-Infrastructure
    }
    "status" {
        Get-StackStatus
    }
    "logs" {
        Get-Logs
    }
    default {
        Write-Host "Usage: .\deploy-windows.ps1 [-Environment <env>] [-Region <region>] [-Action <deploy|destroy|status|logs>]"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  .\deploy-windows.ps1                                    # Deploy to production"
        Write-Host "  .\deploy-windows.ps1 -Environment staging               # Deploy to staging"
        Write-Host "  .\deploy-windows.ps1 -Action destroy                    # Destroy infrastructure"
        Write-Host "  .\deploy-windows.ps1 -Action status                     # Check stack status"
        Write-Host "  .\deploy-windows.ps1 -Action logs                       # View logs"
        exit 1
    }
}