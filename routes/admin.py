from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
import os
from dotenv import load_dotenv
import qrcode
from models import get_all_users, get_user_by_code, update_user_points, get_user_by_identifier, update_user, delete_user
from routes.main import generate_qr_image

admin_bp = Blueprint('admin_bp', __name__)
load_dotenv()

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Admin123')
QR_FOLDER = 'qrcodes'

# Prosty model admina w pamięci
class Admin(UserMixin):
    def __init__(self):
        self.id = "admin"
        self.is_admin = True

admin_user = Admin()

# ----- logowanie -----
@admin_bp.route('/', methods=['GET', 'POST'], endpoint='admin_login')
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            login_user(admin_user)
            flash('Zalogowano jako administrator.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_bp.dashboard'))
        else:
            flash('Nieprawidłowe hasło.', 'danger')
    return render_template('admin_login.html')

# ----- wylogowanie -----
@admin_bp.route('/logout', endpoint='admin_logout')
@login_required
def admin_logout():
    logout_user()
    flash('Zostałeś wylogowany.', 'info')
    return redirect(url_for('admin_bp.admin_login'))

# ----- dekorator dla admina -----
from functools import wraps
from flask import abort

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            abort(403)
        return func(*args, **kwargs)
    return wrapper

# ----- chronione trasy -----
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = get_all_users()
    return render_template('dashboard.html', users=users)

@admin_bp.route('/scan', methods=['POST'])
@login_required
@admin_required
def scan():
    code = request.form['code'].strip()
    user = get_user_by_code(code)
    if user:
        new_points = user['points'] + 1
        update_user_points(user['identifier'], new_points)
        flash(f'Dodano 1 punkt dla {user["identifier"]}. Teraz ma {new_points} punktów.', 'success')
    else:
        flash('Nie znaleziono takiego kodu.', 'danger')
    return redirect(url_for('admin_bp.dashboard'))

@admin_bp.route('/adjust_points', methods=['POST'])
@login_required
@admin_required
def adjust_points():
    identifier = request.form['identifier'].strip()
    points_str = request.form['points'].strip()
    try:
        points = int(points_str)
        if points < 0:
            flash('Liczba punktów nie może być ujemna.', 'danger')
            return redirect(url_for('admin_bp.dashboard'))
    except ValueError:
        flash('Liczba punktów musi być liczbą całkowitą.', 'danger')
        return redirect(url_for('admin_bp.dashboard'))

    user = get_user_by_identifier(identifier)
    if user:
        update_user_points(identifier, points)
        flash(f'Punkty dla {identifier} zostały ustawione na {points}.', 'success')
    else:
        flash(f'Nie znaleziono użytkownika o identyfikatorze: {identifier}.', 'danger')
    return redirect(url_for('admin_bp.dashboard'))

@admin_bp.route('/edit_user/<identifier>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(identifier):
    user = get_user_by_identifier(identifier)
    if not user:
        flash('Użytkownik nie znaleziony.', 'danger')
        return redirect(url_for('admin_bp.dashboard'))

    if request.method == 'POST':
        old_identifier = identifier
        new_identifier = request.form['identifier'].strip()
        new_code = request.form['code'].strip()
        new_points = int(request.form['points'])

        if not new_identifier or not new_code or new_points < 0:
            flash('Wszystkie pola muszą być wypełnione poprawnie.', 'danger')
            return render_template('edit_user.html', user=user)

        success = update_user(old_identifier, new_identifier, new_code, new_points)
        if success:
            if old_identifier != new_identifier and os.path.exists(os.path.join(QR_FOLDER, f'{old_identifier}.png')):
                os.remove(os.path.join(QR_FOLDER, f'{old_identifier}.png'))
            generate_qr_image(new_code, f'{new_identifier}.png')
            flash(f'Dane użytkownika "{new_identifier}" zaktualizowane pomyślnie.', 'success')
            return redirect(url_for('admin_bp.dashboard'))
        else:
            flash('Błąd podczas aktualizacji użytkownika. Nowy identyfikator lub kod może już istnieć.', 'danger')
    return render_template('edit_user.html', user=user)

@admin_bp.route('/delete_user/<identifier>', methods=['POST'])
@login_required
@admin_required
def delete_user_route(identifier):
    user = get_user_by_identifier(identifier)
    if not user:
        flash('Użytkownik nie znaleziony.', 'danger')
        return redirect(url_for('admin_bp.dashboard'))

    delete_user(identifier)
    qr_file_path = os.path.join(QR_FOLDER, f'{identifier}.png')
    if os.path.exists(qr_file_path):
        os.remove(qr_file_path)
        flash(f'Usunięto plik QR dla {identifier}.', 'info')
    flash(f'Użytkownik "{identifier}" został usunięty.', 'success')
    return redirect(url_for('admin_bp.dashboard'))
