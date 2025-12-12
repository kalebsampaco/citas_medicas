# Configuración SQLite temporal para desarrollo
# Descomentar estas líneas y comentar la configuración PostgreSQL si tienes problemas

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Para usar PostgreSQL, descomenta:
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": env("DB_NAME", default="citas"),
#         "USER": env("DB_USER", default="postgres"),
#         "PASSWORD": env("DB_PASSWORD", default="postgres"),
#         "HOST": env("DB_HOST", default="localhost"),
#         "PORT": env("DB_PORT", default="5432"),
#     }
# }
