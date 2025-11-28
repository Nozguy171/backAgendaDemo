from app import create_app
from app.models import db

def run_migrations():
    """
    Este script:
    1. Crea todas las tablas automáticamente.
    2. Inserta el primer tenant si no existe.
    """
    app = create_app()
    with app.app_context():
        db.create_all()

        from app.models import Tenant

        if not Tenant.query.first():
            t = Tenant(
                id="divasspa",
                name="Divas Spa",
                domain="divasspa.demoagenda.shop"
            )
            db.session.add(t)
            db.session.commit()
            print(">>> SEED: Tenant inicial creado")

        print(">>> Migraciones aplicadas automáticamente")

if __name__ == "__main__":
    run_migrations()
