from dotenv import dotenv_values

config = dotenv_values(".env")

port = 5555
max_task = 100000
auto_refresh = True

# db = 'flower.db' # SQL-LITE

basic_auth=[f'admin:{config.get('CELERY_FLOWER_PASSWORD')}']