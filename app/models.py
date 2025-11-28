from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Tenant(db.Model):
    __tablename__ = "tenants"

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100))
    domain = db.Column(db.String(200), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

    # Horarios entre semana
    hours_start_week = db.Column(db.String(10))
    hours_end_week = db.Column(db.String(10))

    # Horario sábado
    hours_start_sat = db.Column(db.String(10))
    hours_end_sat = db.Column(db.String(10))

    working_days = db.Column(db.String(50))

class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey("tenants.id"))
    name = db.Column(db.String(100))
    duration_minutes = db.Column(db.Integer)
    price = db.Column(db.Integer)


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey("tenants.id"))
    phone = db.Column(db.String(20))
    name = db.Column(db.String(100))
    visits = db.Column(db.Integer, default=0)


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey("tenants.id"))
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"))
    date = db.Column(db.Date)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    blocks = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
