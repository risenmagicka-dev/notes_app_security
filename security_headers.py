# security_headers.py
from flask import request

def apply_security_headers(response):
    # Content Security Policy (CSP)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
    )

    # Clickjacking защита
    response.headers['X-Frame-Options'] = 'DENY'

    # MIME-sniff защита
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # HSTS (включать только если есть HTTPS)
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions Policy
    response.headers['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=()'

    # Убираем Server и X-Powered-By
    for header in ['Server', 'X-Powered-By']:
        if header in response.headers:
            del response.headers[header]
    response.headers['Server'] = 'SecureNotes'

    return response

