# app/routes/appointments.py
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from ..models import db, Appointment, Customer, Service
from ..utils.tenants import get_tenant

appointments_bp = Blueprint("appointments", __name__)


def parse_date(date_str: str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def parse_time(time_str: str):
    return datetime.strptime(time_str, "%H:%M").time()


def ranges_overlap(start_a, end_a, start_b, end_b):
    # asume datetime
    return not (end_a <= start_b or start_a >= end_b)


@appointments_bp.post("/")
def create_appointment():
    """
    Endpoint que usa el ADMIN para registrar una cita.

    Body esperado:
    {
      "phone": "6861234567",
      "name": "María",          // opcional si ya existe
      "service_id": 1,
      "date": "2025-11-29",
      "start_time": "10:00"
    }
    """
    tenant = get_tenant()
    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404

    data = request.json or {}
    phone = data.get("phone")
    name = data.get("name")
    service_id = data.get("service_id")
    date_str = data.get("date")
    start_str = data.get("start_time")

    if not all([phone, service_id, date_str, start_str]):
        return jsonify({"error": "phone, service_id, date, start_time are required"}), 400

    # buscar servicio
    service = Service.query.filter_by(
        id=service_id,
        tenant_id=tenant.id
    ).first()
    if not service:
        return jsonify({"error": "Service not found"}), 404

    # buscar o crear cliente
    customer = Customer.query.filter_by(
        tenant_id=tenant.id,
        phone=phone
    ).first()

    if not customer:
        if not name:
            # aquí el front puede interpretar que necesita pedir nombre
            return jsonify({
                "error": "name_required",
                "message": "Customer does not exist, name is required to create it."
            }), 400

        customer = Customer(
            tenant_id=tenant.id,
            phone=phone,
            name=name,
            visits=0
        )
        db.session.add(customer)
        db.session.flush()  # para tener customer.id

    # parse fecha y hora
    try:
        date = parse_date(date_str)
        start_time = parse_time(start_str)
    except ValueError:
        return jsonify({"error": "Invalid date or time format"}), 400

    start_dt = datetime.combine(date, start_time)
    end_dt = start_dt + timedelta(minutes=service.duration_minutes)

    # revisar traslape de citas para ese tenant + día
    same_day_appointments = Appointment.query.filter_by(
        tenant_id=tenant.id,
        date=date
    ).all()

    for appt in same_day_appointments:
        appt_start = datetime.combine(date, appt.start_time)
        appt_end = datetime.combine(date, appt.end_time)
        if ranges_overlap(start_dt, end_dt, appt_start, appt_end):
            return jsonify({
                "error": "time_conflict",
                "message": "Time range overlaps with an existing appointment."
            }), 409

    # crear la cita
    blocks = service.duration_minutes // 5

    new_appt = Appointment(
        tenant_id=tenant.id,
        customer_id=customer.id,
        service_id=service.id,
        date=date,
        start_time=start_dt.time(),
        end_time=end_dt.time(),
        blocks=blocks
    )

    # incrementar visitas
    customer.visits = (customer.visits or 0) + 1

    db.session.add(new_appt)
    db.session.commit()

    return jsonify({
        "ok": True,
        "appointment": {
            "id": new_appt.id,
            "date": new_appt.date.strftime("%Y-%m-%d"),
            "start_time": new_appt.start_time.strftime("%H:%M"),
            "end_time": new_appt.end_time.strftime("%H:%M"),
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "visits": customer.visits
            },
            "service": {
                "id": service.id,
                "name": service.name,
                "duration_minutes": service.duration_minutes
            }
        }
    }), 201


@appointments_bp.get("/day")
def list_day():
    """
    Citas del día para el ADMIN.
    GET /appointments/day?date=2025-11-29

    Si no mandan date → usa hoy.
    """
    tenant = get_tenant()
    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404

    date_str = request.args.get("date")
    if date_str:
        try:
            date = parse_date(date_str)
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400
    else:
        date = datetime.utcnow().date()

    appts = Appointment.query.filter_by(
        tenant_id=tenant.id,
        date=date
    ).all()

    result = []
    for a in appts:
        service = Service.query.get(a.service_id)
        customer = Customer.query.get(a.customer_id)
        result.append({
            "id": a.id,
            "date": a.date.strftime("%Y-%m-%d"),
            "start_time": a.start_time.strftime("%H:%M"),
            "end_time": a.end_time.strftime("%H:%M"),
            "service": {
                "id": service.id if service else None,
                "name": service.name if service else None
            },
            "customer": {
                "id": customer.id if customer else None,
                "name": customer.name if customer else None,
                "phone": customer.phone if customer else None,
                "visits": customer.visits if customer else None
            }
        })

    return jsonify(result)
