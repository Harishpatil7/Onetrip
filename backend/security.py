import hashlib
import os
import hmac
import base64
import json
import time

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-onetrip-123456")
JWT_ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2 with SHA256, returning a formatted string."""
    salt = os.urandom(16)
    iterations = 100000
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plain password against a PBKDF2 SHA256 hashed password."""
    try:
        parts = hashed_password.split('$')
        if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        original_hash = bytes.fromhex(parts[3])
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(dk, original_hash)
    except Exception:
        return False

def base64url_encode(data: bytes) -> str:
    """Helper to base64url encode bytes as per RFC 7515."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    """Helper to base64url decode a string as per RFC 7515."""
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_jwt(payload: dict, expires_in: int = 3600 * 24) -> str:
    """Generate a HS256-signed JWT token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = payload.copy()
    payload["exp"] = int(time.time()) + expires_in
    
    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload).encode('utf-8'))
    
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(JWT_SECRET.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)
    
    return f"{message}.{signature_b64}"

def decode_jwt(token: str) -> dict:
    """Decode and cryptographically verify a HS256 JWT token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        
        message = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
        if not hmac.compare_digest(base64url_decode(signature_b64), expected_sig):
            return None
            
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        if payload.get("exp", 0) < time.time():
            return None # Expired
            
        return payload
    except Exception:
        return None
