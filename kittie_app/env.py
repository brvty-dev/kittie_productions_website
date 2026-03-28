import os
from pathlib import Path
import secrets

ENV_FILE = Path(__file__).parent / '.env.secret'

def load_env_vars():
    """Load or generate a persistent SECRET_KEY."""
    if not ENV_FILE.exists():
        secret_key = secrets.token_hex(32)  # 64-char hex string
        with open(ENV_FILE, 'w') as f:
            f.write(f'SECRET_KEY={secret_key}\n')
    else:
        with open(ENV_FILE) as f:
            for line in f:
                if line.startswith('SECRET_KEY='):
                    secret_key = line.strip().split('=', 1)[1]
                    break
            else:
                raise ValueError("SECRET_KEY not found in .env.secret")

    os.environ['SECRET_KEY'] = secret_key