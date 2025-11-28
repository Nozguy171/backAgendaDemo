from flask import request
from ..models import Tenant

def resolve_tenant_id():
    """
    Solo obtiene el ID (string) desde ?tenant o desde el subdominio.
    """
    # 1️⃣ ?tenant=
    tenant = request.args.get("tenant")
    if tenant:
        return tenant.lower()

    # 2️⃣ Subdominio
    host = request.headers.get("Host", "")
    host = host.split(":")[0]

    if "localhost" in host or "127.0.0.1" in host:
        return None

    parts = host.split(".")
    if len(parts) >= 3:
        return parts[0].lower()

    return None


def get_tenant():
    """
    Regresa el OBJETO Tenant desde la BD.
    """
    tenant_id = resolve_tenant_id()

    if not tenant_id:
        return None

    return Tenant.query.filter_by(id=tenant_id).first()
