import sqlite3
import os

DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Pozwala na dostęp do kolumn jak do słownika
    return conn

def init_db(app):
    # Upewnij się, że operacje na bazie danych są wykonywane w kontekście aplikacji Flask
    # W Pycharmie, uruchamiając 'app.py', context jest już dostępny, ale to jest dobra praktyka.
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            identifier TEXT PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            points INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_user_by_identifier(identifier):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE identifier = ?', (identifier,)).fetchone()
    conn.close()
    return user

def get_user_by_code(code):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE code = ?', (code,)).fetchone()
    conn.close()
    return user

def add_user(identifier, code):
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (identifier, code) VALUES (?, ?)', (identifier, code))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Ten identyfikator lub kod już istnieje
        return False
    finally:
        conn.close()

def update_user_points(identifier, points):
    conn = get_db_connection()
    conn.execute('UPDATE users SET points = ? WHERE identifier = ?', (points, identifier))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY points DESC').fetchall()
    conn.close()
    return users

def update_user(old_identifier, new_identifier, new_code, new_points):
    conn = get_db_connection()
    try:
        # Sprawdź, czy nowy identyfikator już istnieje i nie jest starym identyfikatorem
        if old_identifier != new_identifier:
            existing_user = conn.execute('SELECT identifier FROM users WHERE identifier = ?', (new_identifier,)).fetchone()
            if existing_user:
                return False # Nowy identyfikator już istnieje

        # Sprawdź, czy nowy kod już istnieje i nie jest starym kodem
        if get_user_by_code(new_code) and get_user_by_code(new_code)['identifier'] != old_identifier:
            return False # Nowy kod już istnieje

        conn.execute('UPDATE users SET identifier = ?, code = ?, points = ? WHERE identifier = ?',
                     (new_identifier, new_code, new_points, old_identifier))
        conn.commit()
        return True
    except Exception as e:
        print(f"Błąd aktualizacji użytkownika: {e}")
        return False
    finally:
        conn.close()

def delete_user(identifier):
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE identifier = ?', (identifier,))
    conn.commit()
    conn.close()