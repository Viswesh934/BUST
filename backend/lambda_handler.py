"""
AWS Lambda entrypoint for BUST FastAPI backend.
Configure your Lambda Handler setting as:
  lambda_handler.handler
  or
  app.main.handler
"""
from app.main import app, handler

# Alias for standard Lambda naming
lambda_handler = handler

__all__ = ["app", "handler", "lambda_handler"]
