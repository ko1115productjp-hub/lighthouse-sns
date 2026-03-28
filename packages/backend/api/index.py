"""
Vercel Serverless Function Entry Point

This module serves as the entry point for deploying the FastAPI application
on Vercel Serverless Functions.
"""

from app.main import app

# Vercel expects a variable named 'app' or 'handler'
# FastAPI app is already defined in app.main
handler = app
