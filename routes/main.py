from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
import random
import string
import os
import re
import qrcode
from models import get_user_by_identifier, add_user

main_bp = Blueprint('main_bp', __name__)

QR_FOLDER = 'qrcodes'

def generate_unique_code(identifier):
    # Generuje 10 losowych cyfr i łączy z identyfikatorem dla unikalności
    # Możesz to zmienić na bardziej losowe, np. UUID lub bardziej złożony hash
    return identifier + ''.join(random.choices(string.digits + string.ascii_letters, k=10))

def generate_qr_image(data, filename):
    img = qrcode.make(data)
    path = os.path.join(QR_FOLDER, filename)
    img.save(path)
    return filename

def is_valid_email(email):
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)

# ... (pozostały kod) ...

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        identifier = request.form['identifier'].strip()

        if not (identifier.isdigit() and len(identifier) == 9) and not is_valid_email(identifier):
            flash('Podaj prawidłowy adres email lub 9-cyfrowy numer telefonu.', 'danger')
            return render_template('index.html', booksy_link=current_app.config['BOOKSY_LINK']) # Dodaj booksy_link

        user = get_user_by_identifier(identifier)
        if not user:
            code = generate_unique_code(identifier)
            add_user(identifier, code)
            generate_qr_image(code, f'{identifier}.png')
            flash('Twój kod referencyjny został wygenerowany. Użyj go, aby zdobywać punkty!', 'success')
            return render_template('referral.html', code=code, identifier=identifier, booksy_link=current_app.config['BOOKSY_LINK'])
        else:
            code = user['code']
            if not os.path.exists(os.path.join(QR_FOLDER, f'{identifier}.png')):
                generate_qr_image(code, f'{identifier}.png')
            flash('Twój kod referencyjny jest już dostępny.', 'info')
            return render_template('referral.html', code=code, identifier=identifier, booksy_link=current_app.config['BOOKSY_LINK'])

    return render_template('index.html', booksy_link=current_app.config['BOOKSY_LINK']) # Dodaj booksy_link tutaj

@main_bp.route('/qr/<identifier>', endpoint='qr_image')
def qr_image(identifier):
    path = os.path.join(QR_FOLDER, f'{identifier}.png')
    if os.path.exists(path):
        return send_file(path, mimetype='image/png')
    return 'QR code not found', 404

@main_bp.route('/user_stats', methods=['GET', 'POST'])
def user_stats():
    if request.method == 'POST':
        identifier = request.form['identifier'].strip()

        if not (identifier.isdigit() and len(identifier) == 9) and not is_valid_email(identifier):
            flash('Podaj prawidłowy adres email lub 9-cyfrowy numer telefonu.', 'danger')
            return render_template('user_stats_form.html')

        user = get_user_by_identifier(identifier)
        if user:
            # Upewnij się, że QR kod istnieje
            if not os.path.exists(os.path.join(QR_FOLDER, f'{identifier}.png')):
                generate_qr_image(user['code'], f'{identifier}.png')
            return render_template('user_stats.html', user=user, booksy_link=current_app.config['BOOKSY_LINK'])
        else:
            flash('Nie znaleziono użytkownika o podanym identyfikatorze.', 'danger')
            return render_template('user_stats_form.html')

    return render_template('user_stats_form.html')