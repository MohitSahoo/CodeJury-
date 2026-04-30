# Quick Wins (1-2 Days Each)

## 1. Cache Encryption (Day 1)
```python
# tools/cache_encryption.py
from cryptography.fernet import Fernet
import os

def get_key():
    key = os.getenv('CACHE_ENCRYPTION_KEY')
    if not key:
        key = Fernet.generate_key()
        print(f"Add to .env: CACHE_ENCRYPTION_KEY={key.decode()}")
    return key

def encrypt_cache(data):
    f = Fernet(get_key())
    return f.encrypt(json.dumps(data).encode())

def decrypt_cache(encrypted):
    f = Fernet(get_key())
    return json.loads(f.decrypt(encrypted))
```

## 2. Secrets Detection (Day 1)
```python
# tools/secrets_detector.py
import re

PATTERNS = {
    'api_key': r'[A-Za-z0-9_-]{32,}',
    'aws_key': r'AKIA[0-9A-Z]{16}',
    'private_key': r'-----BEGIN.*PRIVATE KEY-----',
}

def scan_for_secrets(code):
    found = []
    for name, pattern in PATTERNS.items():
        if re.search(pattern, code):
            found.append(name)
    return found
```

## 3. Rate Limit Tracking (Day 2)
```python
# tools/rate_limiter.py
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_calls, window_seconds):
        self.max_calls = max_calls
        self.window = timedelta(seconds=window_seconds)
        self.calls = deque()
    
    def can_call(self):
        now = datetime.now()
        # Remove old calls
        while self.calls and self.calls[0] < now - self.window:
            self.calls.popleft()
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        self.calls.append(datetime.now())
```

## 4. Privacy Policy (Day 2)
Create `PRIVACY.md`:
- What data is sent to APIs (code snippets only)
- How long data is retained (not stored by us)
- Third-party services (Gemini, Groq)
- User rights (can opt out)
