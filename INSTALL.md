# Instalación Backend

## Opción 1: Poetry (recomendado)
```bash
pip install poetry
poetry install
poetry shell
python manage.py migrate
python manage.py runserver
```

## Opción 2: pip + requirements.txt
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Opción 3: Docker
```bash
docker build -t citas-backend .
docker run -p 8000:8000 --env-file .env citas-backend
```

**Nota**: Asegúrate de tener PostgreSQL corriendo en `localhost:5432` o ajusta `.env`
