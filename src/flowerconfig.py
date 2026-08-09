import os
from dotenv import dotenv_values

# Real environment variables (injected by compose) take precedence over any
# .env baked into the image.
config = {**dotenv_values(".env"), **os.environ}

port = 5555
max_task = 100000
auto_refresh = True

# db = 'flower.db' # SQL-LITE

basic_auth=[f"admin:{config.get('CELERY_FLOWER_PASSWORD')}"]