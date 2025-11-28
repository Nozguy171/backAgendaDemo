from app import create_app
from app.migrate import run_migrations

run_migrations()   # <--- aplica migraciones automáticas y seed

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
