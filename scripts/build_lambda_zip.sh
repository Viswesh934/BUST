#!/usr/bin/env bash
# ==============================================================================
# Build AWS Lambda Zip Deployment Package for BUST Backend
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"
BUILD_DIR="${BACKEND_DIR}/build_lambda"
DIST_DIR="${REPO_ROOT}/dist"
ZIP_PATH="${DIST_DIR}/bust-backend-lambda.zip"

echo "======================================================================"
echo "📦 Building AWS Lambda Zip Package..."
echo "======================================================================"

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}" "${DIST_DIR}"

echo "1. Installing production dependencies using Python 3.12..."
/usr/bin/python3.12 -m pip install \
    --no-cache-dir \
    --target "${BUILD_DIR}" \
    -r "${BACKEND_DIR}/requirements.txt"

echo "2. Copying backend application code..."
cp -r "${BACKEND_DIR}/app" "${BUILD_DIR}/"
cp "${BACKEND_DIR}/lambda_handler.py" "${BUILD_DIR}/"
cp "${BACKEND_DIR}/lambda_function.py" "${BUILD_DIR}/"
if [[ -f "${BACKEND_DIR}/.env" ]]; then
    cp "${BACKEND_DIR}/.env" "${BUILD_DIR}/.env"
fi

# Clean up only bytecode caches (preserve *.dist-info for importlib metadata!)
find "${BUILD_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${BUILD_DIR}" -name "*.pyc" -delete 2>/dev/null || true
find "${BUILD_DIR}" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

echo "3. Creating zip archive..."
rm -f "${ZIP_PATH}"
(cd "${BUILD_DIR}" && zip -r -q -9 "${ZIP_PATH}" .)

ZIP_SIZE_MB=$(du -m "${ZIP_PATH}" | cut -f1)
echo "======================================================================"
echo "✅ Lambda Zip Package ready:"
echo "   File: ${ZIP_PATH}"
echo "   Size: ${ZIP_SIZE_MB} MB"
echo "   Handler: lambda_handler.handler"
echo "======================================================================"
