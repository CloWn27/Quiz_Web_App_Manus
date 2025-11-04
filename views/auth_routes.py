# views/auth_routes.py - Authentication routes

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from extensions import db
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    lang = session.get('lang', 'de')
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Bitte alle Felder ausfüllen' if lang == 'de' else 'Please fill all fields', 'error')
            return render_template('auth/login.html', lang=lang)
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['lang'] = user.sprache
            session.permanent = True
            
            # Update last active
            from datetime import datetime, timezone
            user.last_active = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"User logged in: {username}")
            flash('Erfolgreich angemeldet!' if lang == 'de' else 'Successfully logged in!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Ungültige Anmeldedaten' if lang == 'de' else 'Invalid credentials', 'error')
    
    return render_template('auth/login.html', lang=lang)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    lang = session.get('lang', 'de')
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        email = request.form.get('email', '').strip()
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Benutzername muss mindestens 3 Zeichen lang sein' if lang == 'de' 
                         else 'Username must be at least 3 characters')
        
        if not password or len(password) < 6:
            errors.append('Passwort muss mindestens 6 Zeichen lang sein' if lang == 'de' 
                         else 'Password must be at least 6 characters')
        
        if password != password_confirm:
            errors.append('Passwörter stimmen nicht überein' if lang == 'de' 
                         else 'Passwords do not match')
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            errors.append('Benutzername bereits vergeben' if lang == 'de' 
                         else 'Username already taken')
        
        # Check if email exists (if provided)
        if email and User.query.filter_by(email=email).first():
            errors.append('E-Mail bereits registriert' if lang == 'de' 
                         else 'Email already registered')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html', lang=lang)
        
        # Create new user
        try:
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password),
                email=email if email else None,
                sprache=lang
            )
            db.session.add(new_user)
            db.session.commit()
            
            logger.info(f"New user registered: {username}")
            flash('Registrierung erfolgreich! Bitte anmelden.' if lang == 'de' 
                 else 'Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            db.session.rollback()
            flash('Registrierung fehlgeschlagen. Bitte versuche es erneut.' if lang == 'de' 
                 else 'Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html', lang=lang)

@auth_bp.route('/logout')
def logout():
    """User logout"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User logged out: {username}")
    
    flash('Erfolgreich abgemeldet' if session.get('lang', 'de') == 'de' 
         else 'Successfully logged out', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/guest_login', methods=['POST'])
def guest_login():
    """Quick guest login without registration"""
    lang = session.get('lang', 'de')
    guest_name = request.form.get('guest_name', '').strip()
    
    if not guest_name or len(guest_name) < 2:
        flash('Name zu kurz' if lang == 'de' else 'Name too short', 'error')
        return redirect(url_for('main.index'))
    
    # Create temporary guest user
    import uuid
    guest_username = f"guest_{uuid.uuid4().hex[:8]}"
    
    try:
        guest_user = User(
            username=guest_username,
            password_hash=generate_password_hash(uuid.uuid4().hex),  # Random password
            sprache=lang
        )
        db.session.add(guest_user)
        db.session.commit()
        
        session['user_id'] = guest_user.id
        session['username'] = guest_name  # Display name
        session['is_guest'] = True
        session['lang'] = lang
        session.permanent = False  # Guest sessions are not permanent
        
        logger.info(f"Guest user created: {guest_username} (display: {guest_name})")
        return redirect(url_for('main.dashboard'))
    
    except Exception as e:
        logger.error(f"Guest login error: {e}")
        db.session.rollback()
        flash('Fehler beim Gast-Login' if lang == 'de' else 'Guest login error', 'error')
        return redirect(url_for('main.index'))
