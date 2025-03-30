#!/usr/bin/env pwsh
# PowerShell script for deploying the Lambda function

# Create package directory
Write-Host "Creating package directory..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path ./package | Out-Null

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt -t ./package

# Copy Lambda function to package
Write-Host "Copying Lambda function..." -ForegroundColor Cyan
Copy-Item -Path ./lambda_function.py -Destination ./package/

# Create ZIP archive
Write-Host "Creating deployment package..." -ForegroundColor Cyan
Set-Location -Path ./package
Compress-Archive -Path * -DestinationPath ../deployment-package.zip -Force
Set-Location -Path ..

Write-Host "Deployment package created: deployment-package.zip" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Upload this ZIP file to AWS Lambda" -ForegroundColor Yellow
Write-Host "2. Make sure to update the S3 bucket name in your function code" -ForegroundColor Yellow
Write-Host "3. Configure appropriate IAM permissions for S3 access" -ForegroundColor Yellow 