from flask import Blueprint, jsonify, request
from ..models import db, Customer
from ..utils.tenants import get_tenant

customers_bp = Blueprint("customers", __name__)

@customers_bp.post("/check")
def check():
    tenant = get_tenant()
    data = request.json
    phone = data.get("phone")

    customer = Customer.query.filter_by(
        tenant_id=tenant.id, phone=phone
    ).first()

    if customer:
        return jsonify({
            "exists": True,
            "customer": {"id": customer.id, "name": customer.name}
        })

    return jsonify({"exists": False, "need_name": True})

@customers_bp.post("/create")
def create():
    tenant = get_tenant()
    data = request.json or {}
    phone = data.get("phone")
    name = data.get("name")

    if not phone or not name:
        return jsonify({"error": "phone and name are required"}), 400

    customer = Customer(
        tenant_id=tenant.id,
        phone=phone,
        name=name,
        visits=0
    )
    db.session.add(customer)
    db.session.commit()

    return jsonify({
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "visits": customer.visits
    }), 201
