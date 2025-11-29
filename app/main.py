from app import create_app
from app.migrate import run_migrations
from werkzeug.middleware.proxy_fix import ProxyFix

run_migrations()   # <--- aplica migraciones automáticas y seed

app = create_app()

# 🔥 Arregla el HTTPS detrás de nginx
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# 🔥 Fuerza Flask a generar y entender HTTPS
app.config["PREFERRED_URL_SCHEME"] = "https"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
