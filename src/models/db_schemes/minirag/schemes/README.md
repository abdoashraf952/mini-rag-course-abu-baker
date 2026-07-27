## Run alembic Migrations

### configuration

```bash
cp alembic.ini.example alembic.ini
```

- update the alembic.ini file with your database credentials. (`sqlalchemy.url`)

### crsate a new upgrade

```bash
alembic revision --autogenerate -m "a new update"
```

### run the upgrade

```bash
alembic upgrade head
```