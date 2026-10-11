"""
AWS Lambda entrypoint matching default AWS name (lambda_function.py)
Supports:
  lambda_function.lambda_handler
  lambda_function.handler
"""
from app.main import app, handler

lambda_handler = handler

__all__ = ["app", "handler", "lambda_handler"]
