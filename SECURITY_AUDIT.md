# OWASP Top 10 Security Audit - sv ARC Room Booking Application

## Executive Summary
Audit Date: November 18, 2025
Application: sv ARC Room Booking Dashboard
Technology: Flask 3.1.2, Python 3.12

---

## Critical Vulnerabilities Found

### 🔴 CRITICAL: A01:2021 - Broken Access Control

**Issue 1: Secrets in Version Control**
- **Location**: `config.json` (lines 1-5)
- **Risk**: HIGH
- **Details**: Client secrets, tenant IDs exposed in repository
- **Evidence**:
  ```json
  {
    "tenant_id": "d40dae84-6f47-45c7-9678-bfade1152257",
    "client_id": "f78b3d09-359a-46cc-aefc-1f7c349ce5b8",
    "client_secret": "2.28Q~Vp.UFIx_AluJO44sFNvECEk7QOCoIngaiB"
  }
  ```
- **Impact**: Full application compromise, unauthorized Graph API access
- **Recommendation**: 
  - Move secrets to environment variables
  - Use Azure Key Vault
  - Rotate the exposed client_secret immediately
  - Add `config.json` to `.gitignore`

**Issue 2: Missing CSRF Protection**
- **Location**: All POST endpoints
- **Risk**: MEDIUM
- **Details**: No CSRF tokens on forms (booking, working hours updates)
- **Impact**: Attackers can forge requests from authenticated users
- **Recommendation**: Implement Flask-WTF with CSRF protection

---

### 🟡 MEDIUM: A03:2021 - Injection

**Issue 1: Potential XSS in User Data Display**
- **Location**: `templates/dashboard.html` line 47
- **Risk**: MEDIUM
- **Details**: User-provided data (name, email) rendered without explicit escaping
- **Evidence**: `{{ user.name }}` and `{{ user.email }}`
- **Current Status**: Jinja2 auto-escapes by default (PROTECTED)
- **Recommendation**: Verify all user input is validated

**Issue 2: No Input Validation on Meeting Subject**
- **Location**: `app.py` line 381-390
- **Risk**: LOW-MEDIUM
- **Details**: Meeting subject from `request.json` not validated for length/content
- **Recommendation**: Add input validation:
  ```python
  subject = data.get('subject', '').strip()
  if not subject or len(subject) > 255:
      return jsonify({"error": "Invalid subject"}), 400
  ```

---

### 🟡 MEDIUM: A02:2021 - Cryptographic Failures

**Issue 1: Session Secret Key Generated at Runtime**
- **Location**: `app.py` line 11
- **Risk**: MEDIUM
- **Details**: `app.secret_key = secrets.token_hex(32)` regenerates on restart
- **Impact**: All sessions invalidated on service restart
- **Recommendation**: Use persistent secret from environment variable

**Issue 2: No HTTPS Enforcement in Code**
- **Location**: Flask app configuration
- **Risk**: LOW (mitigated by nginx SSL)
- **Details**: Application doesn't force HTTPS
- **Current Status**: nginx handles SSL (MITIGATED)
- **Recommendation**: Add Flask-Talisman for defense in depth

---

### 🟢 LOW: A05:2021 - Security Misconfiguration

**Issue 1: Debug Mode in Production**
- **Location**: `app.py` (implicit)
- **Current Status**: Debug mode appears OFF (GOOD)
- **Verification Needed**: Check systemd service configuration

**Issue 2: No Security Headers**
- **Location**: HTTP responses
- **Risk**: LOW
- **Missing Headers**:
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - Content-Security-Policy
  - Strict-Transport-Security (HSTS)
- **Recommendation**: Add Flask-Talisman or nginx headers

---

### 🟢 LOW: A04:2021 - Insecure Design

**Issue 1: Working Hours Stored Locally**
- **Location**: `room_working_hours.json`
- **Risk**: LOW
- **Details**: Data loss if file deleted, no backup mechanism
- **Recommendation**: Consider database storage or automated backups

---

### 🟢 LOW: A07:2021 - Identification and Authentication Failures

**Issue 1: No Rate Limiting on Login**
- **Location**: `/arcrooms/login` endpoint
- **Risk**: LOW-MEDIUM
- **Details**: No protection against brute force on OAuth flow
- **Recommendation**: Implement rate limiting with Flask-Limiter

**Issue 2: Session Timeout Not Configured**
- **Location**: Flask session configuration
- **Risk**: LOW
- **Details**: Sessions may persist indefinitely
- **Recommendation**: Set `PERMANENT_SESSION_LIFETIME`

---

## Vulnerabilities NOT Present (Good Security Practices)

✅ **A06:2021 - Vulnerable Components**: Using recent Flask 3.1.2  
✅ **A08:2021 - Software Integrity**: No client-side dependencies from CDNs  
✅ **A09:2021 - Logging Failures**: Systemd handles logging  
✅ **A10:2021 - SSRF**: Graph API calls use fixed endpoints  
✅ **SQL Injection**: No SQL database used  
✅ **Path Traversal**: Static files served by Flask safely  
✅ **Authentication**: OAuth 2.0 with Microsoft properly implemented  
✅ **Authorization**: Delegate checking implemented for admin functions  

---

## Immediate Action Items (Priority Order)

1. **CRITICAL**: Rotate `client_secret` and move to environment variables
2. **HIGH**: Add CSRF protection to all forms
3. **HIGH**: Implement input validation on all user inputs
4. **MEDIUM**: Use persistent session secret key
5. **MEDIUM**: Add security headers via Flask-Talisman
6. **MEDIUM**: Implement rate limiting
7. **LOW**: Configure session timeout
8. **LOW**: Add automated backups for working_hours.json

---

## Code Remediation Examples

### 1. Environment Variables for Secrets
```python
import os
from dotenv import load_dotenv

load_dotenv()

TENANT = os.getenv('AZURE_TENANT_ID')
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')

if not all([TENANT, CLIENT_ID, CLIENT_SECRET]):
    raise ValueError("Missing required environment variables")
```

### 2. CSRF Protection
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# In HTML forms:
# <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

### 3. Security Headers
```python
from flask_talisman import Talisman

Talisman(app, 
    force_https=True,
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'"
    }
)
```

### 4. Input Validation
```python
def validate_meeting_request(data):
    errors = []
    
    subject = data.get('subject', '').strip()
    if not subject:
        errors.append("Subject is required")
    elif len(subject) > 255:
        errors.append("Subject too long (max 255 chars)")
    
    notes = data.get('notes', '').strip()
    if len(notes) > 1000:
        errors.append("Notes too long (max 1000 chars)")
    
    return errors
```

### 5. Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.get("/arcrooms/login")
@limiter.limit("10 per minute")
def login():
    # ...
```

---

## Overall Security Score: 6.5/10

**Strengths**:
- OAuth 2.0 authentication properly implemented
- Delegate authorization checks in place
- Jinja2 auto-escaping prevents basic XSS
- No SQL injection vectors
- HTTPS enforced by nginx

**Weaknesses**:
- Secrets exposed in repository
- No CSRF protection
- Missing security headers
- No rate limiting
- Runtime-generated session secret

**Recommendation**: Address critical and high priority issues before production use with sensitive data.
