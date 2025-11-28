from flask import Blueprint, request, jsonify
from ..utils.tenants import get_tenant

tenants_bp = Blueprint("tenants", __name__)

@tenants_bp.get("/me")
def me():
    tenant = get_tenant()
    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404
    return jsonify({"id": tenant.id, "name": tenant.name})
