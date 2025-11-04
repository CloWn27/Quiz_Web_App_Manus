# views/game_routes.py - Game-related routes

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import (
    SpielSitzung, SpielTeilnahme, User, Lernfeld, Frage, 
    Spielmodus, Schwierigkeit
)
from extensions import db
import logging
import random
import string

logger = logging.getLogger(__name__)

game_bp = Blueprint('game', __name__)

def generate_room_code():
    """Generate a unique 6-character room code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not SpielSitzung.query.filter_by(raum_code=code).first():
            return code

@game_bp.route('/join', methods=['GET', 'POST'])
def join():
    """Join a game with room code"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    lang = session.get('lang', 'de')
    
    if request.method == 'POST':
        room_code = request.form.get('room_code', '').strip().upper()
        
        if not room_code:
            flash('Bitte Raum-Code eingeben' if lang == 'de' else 'Please enter room code', 'error')
            return render_template('game/join.html', lang=lang)
        
        sitzung = SpielSitzung.query.filter_by(raum_code=room_code, ist_aktiv=True).first()
        
        if not sitzung:
            flash('Spiel nicht gefunden' if lang == 'de' else 'Game not found', 'error')
            return render_template('game/join.html', lang=lang)
        
        # Check if user already joined
        teilnahme = SpielTeilnahme.query.filter_by(
            sitzung_id=sitzung.id,
            user_id=session['user_id']
        ).first()
        
        if not teilnahme:
            # Create new participation
            teilnahme = SpielTeilnahme(
                sitzung_id=sitzung.id,
                user_id=session['user_id']
            )
            db.session.add(teilnahme)
            db.session.commit()
            logger.info(f"User {session['user_id']} joined game {room_code}")
        
        return redirect(url_for('game.lobby', room_code=room_code))
    
    return render_template('game/join.html', lang=lang)

@game_bp.route('/lobby/<room_code>')
def lobby(room_code):
    """Game lobby - waiting for game to start"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    if not sitzung:
        flash('Spiel nicht gefunden', 'error')
        return redirect(url_for('game.join'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    # Get all participants
    teilnehmer = (
        db.session.query(User)
        .join(SpielTeilnahme)
        .filter(SpielTeilnahme.sitzung_id == sitzung.id)
        .all()
    )
    
    # Check if user is the host
    is_host = (sitzung.ersteller_id == session['user_id'])
    
    return render_template(
        'game/lobby.html',
        sitzung=sitzung,
        teilnehmer=teilnehmer,
        is_host=is_host,
        user=user,
        lang=lang
    )

@game_bp.route('/play/<room_code>')
def play(room_code):
    """Main game view"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    if not sitzung:
        flash('Spiel nicht gefunden', 'error')
        return redirect(url_for('game.join'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    # Get user's participation
    teilnahme = SpielTeilnahme.query.filter_by(
        sitzung_id=sitzung.id,
        user_id=session['user_id']
    ).first()
    
    if not teilnahme:
        flash('Du bist nicht Teil dieses Spiels', 'error')
        return redirect(url_for('game.join'))
    
    # Check if user is host
    is_host = (sitzung.ersteller_id == session['user_id'])
    
    return render_template(
        'game/play.html',
        sitzung=sitzung,
        teilnahme=teilnahme,
        is_host=is_host,
        user=user,
        lang=lang
    )

@game_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create a new game session"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    if request.method == 'POST':
        lernfeld_id = request.form.get('lernfeld_id', type=int)
        modus = request.form.get('modus', 'KLASSISCH')
        schwierigkeit = request.form.get('schwierigkeit', 'MITTEL')
        
        # Validate
        if not lernfeld_id:
            flash('Bitte Lernfeld auswählen' if lang == 'de' else 'Please select learning field', 'error')
            return redirect(url_for('game.create'))
        
        lernfeld = Lernfeld.query.get(lernfeld_id)
        if not lernfeld:
            flash('Lernfeld nicht gefunden' if lang == 'de' else 'Learning field not found', 'error')
            return redirect(url_for('game.create'))
        
        # Check if lernfeld has questions
        fragen_count = Frage.query.filter_by(lernfeld_id=lernfeld_id).count()
        if fragen_count == 0:
            flash('Keine Fragen in diesem Lernfeld' if lang == 'de' else 'No questions in this learning field', 'error')
            return redirect(url_for('game.create'))
        
        try:
            # Create game session
            room_code = generate_room_code()
            
            sitzung = SpielSitzung(
                raum_code=room_code,
                modus=Spielmodus[modus],
                schwierigkeit_level=Schwierigkeit[schwierigkeit],
                lernfeld_id=lernfeld_id,
                ersteller_id=session['user_id']
            )
            db.session.add(sitzung)
            db.session.commit()
            
            # Automatically join as host
            teilnahme = SpielTeilnahme(
                sitzung_id=sitzung.id,
                user_id=session['user_id']
            )
            db.session.add(teilnahme)
            db.session.commit()
            
            logger.info(f"Game created: {room_code} by user {session['user_id']}")
            return redirect(url_for('game.lobby', room_code=room_code))
        
        except Exception as e:
            logger.error(f"Error creating game: {e}")
            db.session.rollback()
            flash('Fehler beim Erstellen des Spiels' if lang == 'de' else 'Error creating game', 'error')
    
    # GET request - show create form
    lernfelder = Lernfeld.query.all()
    
    return render_template(
        'game/create.html',
        lernfelder=lernfelder,
        spielmodi=Spielmodus,
        schwierigkeiten=Schwierigkeit,
        user=user,
        lang=lang
    )

@game_bp.route('/solo', methods=['GET', 'POST'])
def solo():
    """Solo training mode (unranked)"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    if request.method == 'POST':
        lernfeld_id = request.form.get('lernfeld_id', type=int)
        schwierigkeit = request.form.get('schwierigkeit', 'MITTEL')
        fragen_anzahl = request.form.get('fragen_anzahl', 10, type=int)
        
        if not lernfeld_id:
            flash('Bitte Lernfeld auswählen' if lang == 'de' else 'Please select learning field', 'error')
            return redirect(url_for('game.solo'))
        
        # Create solo session
        try:
            room_code = generate_room_code()
            
            sitzung = SpielSitzung(
                raum_code=room_code,
                modus=Spielmodus.SOLO,
                schwierigkeit_level=Schwierigkeit[schwierigkeit],
                lernfeld_id=lernfeld_id,
                ersteller_id=session['user_id']
            )
            db.session.add(sitzung)
            db.session.commit()
            
            # Join solo session
            teilnahme = SpielTeilnahme(
                sitzung_id=sitzung.id,
                user_id=session['user_id']
            )
            db.session.add(teilnahme)
            db.session.commit()
            
            logger.info(f"Solo session created: {room_code}")
            return redirect(url_for('game.play', room_code=room_code))
        
        except Exception as e:
            logger.error(f"Error creating solo session: {e}")
            db.session.rollback()
            flash('Fehler beim Starten des Solo-Modus' if lang == 'de' else 'Error starting solo mode', 'error')
    
    lernfelder = Lernfeld.query.all()
    
    return render_template(
        'game/solo.html',
        lernfelder=lernfelder,
        schwierigkeiten=Schwierigkeit,
        user=user,
        lang=lang
    )

@game_bp.route('/results/<room_code>')
def results(room_code):
    """Display game results"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    if not sitzung:
        flash('Spiel nicht gefunden', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    # Get all participants with scores
    teilnehmer_results = (
        db.session.query(User, SpielTeilnahme)
        .join(SpielTeilnahme, User.id == SpielTeilnahme.user_id)
        .filter(SpielTeilnahme.sitzung_id == sitzung.id)
        .order_by(SpielTeilnahme.aktueller_punktestand.desc())
        .all()
    )
    
    # Get current user's result
    user_teilnahme = SpielTeilnahme.query.filter_by(
        sitzung_id=sitzung.id,
        user_id=session['user_id']
    ).first()
    
    return render_template(
        'game/results.html',
        sitzung=sitzung,
        teilnehmer_results=teilnehmer_results,
        user_teilnahme=user_teilnahme,
        user=user,
        lang=lang
    )
