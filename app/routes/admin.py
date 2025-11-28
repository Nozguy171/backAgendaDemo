# app/routes/admin.py
from flask import Blueprint, request, jsonify
from ..models import db, Tenant, Service, Customer, Appointment
from datetime import datetime, timedelta
from ..utils.tenants import get_tenant

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# -------------------------
#  BOOTSTRAP TENANT
# -------------------------

@admin_bp.route("/bootstrap/create-tenant", methods=["POST"])
def bootstrap_create_tenant():
    data = request.json
    name = data.get("name")
    tenant_id = data.get("tenant_id")

    if not name or not tenant_id:
        return {"error": "Missing name or tenant_id"}, 400

    exists = Tenant.query.filter_by(id=tenant_id).first()
    if exists:
        return {"error": "Tenant already exists"}, 400

    t = Tenant(id=tenant_id, name=name)
    db.session.add(t)
    db.session.commit()

    return {"ok": True, "tenant": {"id": t.id, "name": t.name}}


# -------------------------
#  SETTINGS (NEGOCIO)
# -------------------------
@admin_bp.get("/settings")
def get_settings():
    tenant = get_tenant()

    working_days = (
        list(map(int, tenant.working_days.split(",")))
        if tenant.working_days else [1,2,3,4,5,6]
    )

    return jsonify({
        "name": tenant.name,
        "phone": tenant.phone,

        "weekStart": tenant.hours_start_week,
        "weekEnd": tenant.hours_end_week,

        "satStart": tenant.hours_start_sat,
        "satEnd": tenant.hours_end_sat,

        "workingDays": working_days,
    })


@admin_bp.put("/settings")
def update_settings():
    tenant = get_tenant()
    data = request.json or {}

    tenant.name = data.get("name", tenant.name)
    tenant.phone = data.get("phone", tenant.phone)

    tenant.hours_start_week = data.get("weekStart", tenant.hours_start_week)
    tenant.hours_end_week = data.get("weekEnd", tenant.hours_end_week)

    tenant.hours_start_sat = data.get("satStart", tenant.hours_start_sat)
    tenant.hours_end_sat = data.get("satEnd", tenant.hours_end_sat)

    if "workingDays" in data:
        tenant.working_days = ",".join(str(x) for x in data["workingDays"])

    db.session.commit()
    return jsonify({"message": "Settings updated"})

# -------------------------
#  SERVICES CRUD
# -------------------------

def service_to_dict(s: Service):
    return {
        "id": s.id,
        "tenantId": s.tenant_id,
        "name": s.name,
        "durationMinutes": s.duration_minutes,
        "price": s.price,
    }


@admin_bp.get("/services")
def list_services():
    tenant_id = request.args.get("tenant")
    services = Service.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([service_to_dict(s) for s in services])


@admin_bp.post("/services")
def create_service():
    tenant_id = request.args.get("tenant")
    data = request.json or {}

    # Permitimos duration o durationMinutes
    duration = data.get("durationMinutes", data.get("duration"))
    if duration is None:
        return jsonify({"error": "Missing duration/durationMinutes"}), 400

    service = Service(
        tenant_id=tenant_id,
        name=data["name"],
        duration_minutes=duration,
        price=data.get("price", 0),
    )
    db.session.add(service)
    db.session.commit()

    return jsonify(service_to_dict(service)), 201


@admin_bp.put("/services/<int:service_id>")
def update_service(service_id):
    data = request.json or {}
    service = Service.query.get_or_404(service_id)

    service.name = data.get("name", service.name)

    duration = data.get("durationMinutes", data.get("duration"))
    if duration is not None:
        service.duration_minutes = duration

    if "price" in data:
        service.price = data["price"]

    db.session.commit()

    return jsonify(service_to_dict(service))


@admin_bp.delete("/services/<int:service_id>")
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({"message": "Deleted"})


# -------------------------
#  APPOINTMENTS HELPERS
# -------------------------

def appointment_to_dict(a: Appointment):
    return {
        "id": a.id,
        "tenantId": a.tenant_id,
        "customerId": a.customer_id,
        "serviceId": a.service_id,
        "date": a.date.isoformat() if a.date else None,
        "startTime": a.start_time.strftime("%H:%M") if a.start_time else None,
        "endTime": a.end_time.strftime("%H:%M") if a.end_time else None,
        "blocks": a.blocks,
        "createdAt": a.created_at.isoformat() if a.created_at else None,
    }


# -------------------------
#  APPOINTMENTS: DAY
# -------------------------

@admin_bp.get("/appointments/day")
def appointments_day():
    tenant_id = request.args.get("tenant")
    date_str = request.args.get("date")  # YYYY-MM-DD

    if not date_str:
        return jsonify({"error": "Missing date (YYYY-MM-DD)"}), 400

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format, expected YYYY-MM-DD"}), 400

    appts = Appointment.query.filter(
        Appointment.tenant_id == tenant_id,
        Appointment.date == date_obj,
    ).all()

    return jsonify([appointment_to_dict(a) for a in appts])


# -------------------------
#  APPOINTMENTS: WEEK
# -------------------------

@admin_bp.get("/appointments/week")
def appointments_week():
    tenant_id = request.args.get("tenant")
    start_str = request.args.get("start")  # YYYY-MM-DD

    if not start_str:
        return jsonify({"error": "Missing start (YYYY-MM-DD)"}), 400

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid start format, expected YYYY-MM-DD"}), 400

    end_date = start_date + timedelta(days=7)

    appts = Appointment.query.filter(
        Appointment.tenant_id == tenant_id,
        Appointment.date >= start_date,
        Appointment.date < end_date,
    ).all()

    return jsonify([appointment_to_dict(a) for a in appts])


# -------------------------
#  APPOINTMENTS: MONTH
# -------------------------

@admin_bp.get("/appointments/month")
def appointments_month():
    tenant_id = request.args.get("tenant")
    month_str = request.args.get("month")  # YYYY-MM

    if not month_str:
        return jsonify({"error": "Missing month (YYYY-MM)"}), 400

    try:
        year, month = map(int, month_str.split("-"))
    except ValueError:
        return jsonify({"error": "Invalid month format, expected YYYY-MM"}), 400

    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    appts = Appointment.query.filter(
        Appointment.tenant_id == tenant_id,
        Appointment.date >= start_date,
        Appointment.date < end_date,
    ).all()

    return jsonify([appointment_to_dict(a) for a in appts])


# -------------------------
#  APPOINTMENTS: CREATE
# -------------------------

@admin_bp.post("/appointments")
def create_appointment():
    data = request.json or {}

    tenant_id = data.get("tenant")
    if not tenant_id:
        return jsonify({"error": "Missing tenant"}), 400

    try:
        start_dt = datetime.fromisoformat(data["start"])
        end_dt = datetime.fromisoformat(data["end"])
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid or missing start/end ISO datetimes"}), 400

    appt = Appointment(
        tenant_id=tenant_id,
        service_id=data["serviceId"],
        customer_id=data["customerId"],
        date=start_dt.date(),
        start_time=start_dt.time(),
        end_time=end_dt.time(),
        blocks=data.get("blocks"),
    )

    db.session.add(appt)
    db.session.commit()

    return jsonify(appointment_to_dict(appt)), 201
