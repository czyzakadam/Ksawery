from flask import Flask, redirect, url_for, session, flash
import os
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Import Blueprints
from routes.main import main_bp
from routes.admin import admin_bp
from models import init_db

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'super_secret_key_default') # Użyj zmiennej środowiskowej lub domyślnej
app.config['BOOKSY_LINK'] = 'https://siercutz.booksy.com' # Link Booksy w konfiguracji aplikacji

# Inicjalizacja bazy danych
# init_db(app) musi być wywołane po utworzeniu obiektu Flask 'app'
# ale przed pierwszym requestem, np. w kontekście aplikacji
with app.app_context():
    init_db(app)

# Rejestracja Blueprintów
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')

# Upewnij się, że folder na QR kody istnieje
QR_FOLDER = 'qrcodes'
os.makedirs(QR_FOLDER, exist_ok=True)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Zostałeś wylogowany.', 'info')
    return redirect(url_for('main_bp.index'))

if __name__ == '__main__':
    app.run(debug=True)