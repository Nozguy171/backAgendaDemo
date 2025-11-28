from flask import Blueprint, request, jsonify
from app.models import db, Tenant, Appointment, Service
from datetime import datetime, timedelta, time

availability_bp = Blueprint("availability", __name__)

@availability_bp.route("/availability/week", methods=["GET"])
def get_week_availability():
    tenant_name = request.args.get("tenant")
    if not tenant_name:
        return jsonify({"error": "tenant required"}), 400

    tenant = Tenant.query.filter_by(domain=f"{tenant_name}.demoagenda.shop").first()
    if not tenant:
        return jsonify({"error": "tenant not found"}), 404

    # ============================
    # 🔥 HORARIOS POR DÍA
    # ============================
    week_start = tenant.hours_start_week or "10:00"
    week_end   = tenant.hours_end_week or "19:00"

    sat_start = tenant.hours_start_sat or "10:00"
    sat_end   = tenant.hours_end_sat or "16:00"

    # ============================
    # 🔥 DÍAS LABORALES
    # ============================
    if tenant.working_days:
        working_days = list(map(int, tenant.working_days.split(",")))
    else:
        working_days = [1,2,3,4,5,6]  # default

    # ============================
    # 🔥 Cargar citas próximas 7 días
    # ============================
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=7)

    appts = Appointment.query.filter(
        Appointment.tenant_id == tenant.id,
        Appointment.date >= today,
        Appointment.date <= end_date
    ).all()

    # ============================
    # 🔥 GENERAR BUSY SLOTS (cada 15 min)
    # ============================
    busy = []
    for a in appts:
        start_dt = datetime.combine(a.date, a.start_time)
        end_dt = datetime.combine(a.date, a.end_time)

        block = start_dt
        while block < end_dt:
            busy.append({
                "start": block.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": (block + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S")
            })
            block += timedelta(minutes=15)

    # ============================
    # 🔥 Servicios disponibles
    # ============================
    services = Service.query.filter_by(tenant_id=tenant.id).all()
    services_data = [
        {"id": s.id, "name": s.name, "duration": s.duration_minutes}
        for s in services
    ]

    # ============================
    # 🔥 RESPUESTA COMPLETA
    # ============================
    return jsonify({
        "workingDays": working_days,

        # 👉 FRONT RECIBE LOS DOS HORARIOS
        "weekStart": week_start,
        "weekEnd": week_end,
        "satStart": sat_start,
        "satEnd": sat_end,

        "busySlots": busy,
        "services": services_data
    })
