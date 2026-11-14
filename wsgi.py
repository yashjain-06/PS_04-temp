"""Production entry point:  gunicorn wsgi:app ...   (see docs/deployment.md)"""
from web.app import create_app

app = create_app()
