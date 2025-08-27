from flask import Flask
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv()

# Import Blueprints
from routes.main import main_bp
from routes.admin import admin_bp, admin_user, Admin
from models import init_db

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'super_secret_key_default')
app.config['BOOKSY_LINK'] = 'https://siercutz.booksy.com'

# ---- Flask-Login ----
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_bp.admin_login'

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return admin_user
    return None

# Inicjalizacja bazy
with app.app_context():
    init_db(app)

# Rejestracja blueprintów
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')

# Folder na QR
QR_FOLDER = 'qrcodes'
os.makedirs(QR_FOLDER, exist_ok=True)

if __name__ == '__main__':
    app.run(debug=True)
