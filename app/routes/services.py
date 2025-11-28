# app/routes/services.py
from flask import Blueprint, request, jsonify
from ..models import db, Service
from ..utils.tenants import get_tenant

services_bp = Blueprint("services", __name__)

@services_bp.get("/")
def list_services():
    tenant = get_tenant()
    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404

    services = Service.query.filter_by(tenant_id=tenant.id).all()
    return jsonify([
        {
            "id": s.id,
            "name": s.name,
            "duration_minutes": s.duration_minutes,
            "price": s.price
        } for s in services
    ])


@services_bp.post("/")
def create_service():
    tenant = get_tenant()
    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404

    data = request.json or {}
    name = data.get("name")
    duration_minutes = data.get("duration_minutes")
    price = data.get("price", 0)

    if not name or not duration_minutes:
        return jsonify({"error": "name and duration_minutes are required"}), 400

    service = Service(
        tenant_id=tenant.id,
        name=name,
        duration_minutes=duration_minutes,
        price=price,
    )
    db.session.add(service)
    db.session.commit()

    return jsonify({
        "id": service.id,
        "name": service.name,
        "duration_minutes": service.duration_minutes,
        "price": service.price
    }), 201


@services_bp.put("/<int:service_id>")
def update_service(service_id):
    tenant = get_tenant()
    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404

    service = Service.query.filter_by(
        id=service_id,
        tenant_id=tenant.id
    ).first()

    if not service:
        return jsonify({"error": "Service not found"}), 404

    data = request.json or {}
    if "name" in data:
        service.name = data["name"]
    if "duration_minutes" in data:
        service.duration_minutes = data["duration_minutes"]
    if "price" in data:
        service.price = data["price"]

    db.session.commit()

    return jsonify({
        "id": service.id,
        "name": service.name,
        "duration_minutes": service.duration_minutes,
        "price": service.price
    })


@services_bp.delete("/<int:service_id>")
def delete_service(service_id):
    tenant = get_tenant()
    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404

    service = Service.query.filter_by(
        id=service_id,
        tenant_id=tenant.id
    ).first()

    if not service:
        return jsonify({"error": "Service not found"}), 404

    db.session.delete(service)
    db.session.commit()

    return jsonify({"ok": True})
