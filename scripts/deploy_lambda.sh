#!/usr/bin/env bash
# ==============================================================================
# BUST Backend AWS Lambda Automated Deployment Script
# Deploys FastAPI backend to AWS Lambda with an HTTPS Function URL
# ==============================================================================
set -euo pipefail

FUNCTION_NAME="bust-backend"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_ZIP="${REPO_ROOT}/dist/bust-backend-lambda.zip"
ENV_FILE="${REPO_ROOT}/backend/.env"

echo "======================================================================"
echo "🚀 Deploying BUST Backend to AWS Lambda (${REGION})"
echo "======================================================================"

# 1. Verify AWS CLI credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ Error: AWS CLI credentials not found or invalid."
    echo "Please run 'aws configure' first or set AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
echo "✅ Authenticated as AWS Account: ${ACCOUNT_ID}"

# 2. Build deployment package
echo "📦 Building Lambda package..."
"${SCRIPT_DIR}/build_lambda_zip.sh"

if [[ ! -f "${DIST_ZIP}" ]]; then
    echo "❌ Zip file not found at ${DIST_ZIP}"
    exit 1
fi

# 3. Read environment variables from backend/.env
echo "🔐 Loading environment variables..."
ENV_VARS="AWS_LAMBDA_FUNCTION_NAME=${FUNCTION_NAME}"

if [[ -f "${ENV_FILE}" ]]; then
    while IFS='=' read -r key val || [[ -n "$key" ]]; do
        # Ignore comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        # Strip quotes and spaces
        key=$(echo "$key" | tr -d '[:space:]')
        val=$(echo "$val" | tr -d '\r' | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
        if [[ -n "$key" && -n "$val" ]]; then
            ENV_VARS="${ENV_VARS},${key}=${val}"
        fi
    done < "${ENV_FILE}"
fi

# 4. Check or create IAM execution role
ROLE_NAME="bust-backend-lambda-role"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

if ! aws iam get-role --role-name "${ROLE_NAME}" > /dev/null 2>&1; then
    echo "👤 Creating IAM Role '${ROLE_NAME}'..."
    TRUST_POLICY='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    aws iam create-role \
        --role-name "${ROLE_NAME}" \
        --assume-role-policy-document "${TRUST_POLICY}" \
        --description "Execution role for BUST Backend Lambda" > /dev/null
    
    aws iam attach-role-policy \
        --role-name "${ROLE_NAME}" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    echo "⏳ Waiting 10s for IAM role replication..."
    sleep 10
else
    echo "✅ Using existing IAM role: ${ROLE_ARN}"
fi

# 5. Create or update Lambda function
if aws lambda get-function --function-name "${FUNCTION_NAME}" --region "${REGION}" > /dev/null 2>&1; then
    echo "🔄 Updating existing Lambda function code..."
    aws lambda update-function-code \
        --function-name "${FUNCTION_NAME}" \
        --zip-file "fileb://${DIST_ZIP}" \
        --region "${REGION}" > /dev/null

    echo "⏳ Waiting for code update to complete..."
    aws lambda wait function-updated --function-name "${FUNCTION_NAME}" --region "${REGION}"

    echo "⚙️ Updating function configuration (timeout: 60s, memory: 512MB, env vars)..."
    aws lambda update-function-configuration \
        --function-name "${FUNCTION_NAME}" \
        --timeout 60 \
        --memory-size 512 \
        --handler "lambda_handler.handler" \
        --environment "Variables={${ENV_VARS}}" \
        --region "${REGION}" > /dev/null
else
    echo "✨ Creating new Lambda function '${FUNCTION_NAME}'..."
    aws lambda create-function \
        --function-name "${FUNCTION_NAME}" \
        --runtime "python3.12" \
        --role "${ROLE_ARN}" \
        --handler "lambda_handler.handler" \
        --zip-file "fileb://${DIST_ZIP}" \
        --timeout 60 \
        --memory-size 512 \
        --environment "Variables={${ENV_VARS}}" \
        --region "${REGION}" > /dev/null
fi

echo "⏳ Waiting for function to be active..."
aws lambda wait function-active --function-name "${FUNCTION_NAME}" --region "${REGION}"

# 6. Enable or retrieve Lambda Function URL with CORS
echo "🌐 Configuring HTTPS Function URL..."
URL_CONFIG=$(aws lambda get-function-url-config --function-name "${FUNCTION_NAME}" --region "${REGION}" 2>/dev/null || true)

if [[ -z "${URL_CONFIG}" ]]; then
    FUNCTION_URL=$(aws lambda create-function-url-config \
        --function-name "${FUNCTION_NAME}" \
        --auth-type "NONE" \
        --cors '{"AllowOrigins":["*"],"AllowMethods":["*"],"AllowHeaders":["*"],"ExposeHeaders":["*"]}' \
        --region "${REGION}" \
        --query "FunctionUrl" \
        --output text)

    # Grant public invoke permissions
    aws lambda add-permission \
        --function-name "${FUNCTION_NAME}" \
        --statement-id "FunctionURLAllowPublicAccess" \
        --action "lambda:InvokeFunctionUrl" \
        --principal "*" \
        --function-url-auth-type "NONE" \
        --region "${REGION}" > /dev/null || true
else
    FUNCTION_URL=$(aws lambda get-function-url-config \
        --function-name "${FUNCTION_NAME}" \
        --region "${REGION}" \
        --query "FunctionUrl" \
        --output text)
fi

# Remove trailing slash
CLEAN_URL="${FUNCTION_URL%/}"

echo ""
echo "======================================================================"
echo "🎉 BUST Backend is live on AWS Lambda!"
echo "   Lambda URL: ${CLEAN_URL}"
echo "   Health Check: ${CLEAN_URL}/api/health"
echo "   Docs:        ${CLEAN_URL}/docs"
echo "======================================================================"
echo ""
echo "🚀 NEXT STEP FOR VERCEL FRONTEND:"
echo "In your Vercel Project Settings -> Environment Variables, add:"
echo "   PUBLIC_BACKEND_URL=${CLEAN_URL}"
echo "======================================================================"
