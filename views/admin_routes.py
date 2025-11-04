# views/admin_routes.py - Admin/Spielleiter routes

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import (
    SpielSitzung, User, Lernfeld, Frage, Antwort, 
    TextAntwortSchluessel, Fragetyp, Schwierigkeit
)
from extensions import db
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

def is_admin():
    """Check if current user is admin (simplified - in production use proper role system)"""
    # For now, any logged-in user can access admin
    # TODO: Implement proper admin role system
    return 'user_id' in session

@admin_bp.route('/')
def index():
    """Admin dashboard"""
    if not is_admin():
        flash('Zugriff verweigert', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'total_games': SpielSitzung.query.count(),
        'active_games': SpielSitzung.query.filter_by(ist_aktiv=True).count(),
        'total_questions': Frage.query.count(),
        'total_lernfelder': Lernfeld.query.count()
    }
    
    # Get recent games
    recent_games = (
        SpielSitzung.query
        .order_by(SpielSitzung.created_at.desc())
        .limit(10)
        .all()
    )
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_games=recent_games,
        user=user,
        lang=lang
    )

@admin_bp.route('/questions')
def questions():
    """Manage questions"""
    if not is_admin():
        flash('Zugriff verweigert', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    # Get filter parameters
    lernfeld_id = request.args.get('lernfeld_id', type=int)
    schwierigkeit = request.args.get('schwierigkeit')
    
    # Build query
    query = Frage.query
    
    if lernfeld_id:
        query = query.filter_by(lernfeld_id=lernfeld_id)
    
    if schwierigkeit:
        query = query.filter_by(schwierigkeit=Schwierigkeit[schwierigkeit])
    
    fragen = query.order_by(Frage.id.desc()).all()
    lernfelder = Lernfeld.query.all()
    
    return render_template(
        'admin/questions.html',
        fragen=fragen,
        lernfelder=lernfelder,
        schwierigkeiten=Schwierigkeit,
        user=user,
        lang=lang
    )

@admin_bp.route('/questions/add', methods=['GET', 'POST'])
def add_question():
    """Add new question"""
    if not is_admin():
        flash('Zugriff verweigert', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    if request.method == 'POST':
        try:
            # Get form data
            lernfeld_id = request.form.get('lernfeld_id', type=int)
            typ = request.form.get('typ')
            schwierigkeit = request.form.get('schwierigkeit')
            frage_text_de = request.form.get('frage_text_de', '').strip()
            frage_text_en = request.form.get('frage_text_en', '').strip()
            zeitlimit_sek = request.form.get('zeitlimit_sek', 30, type=int)
            
            # Validate
            if not all([lernfeld_id, typ, schwierigkeit, frage_text_de, frage_text_en]):
                flash('Bitte alle Felder ausfüllen' if lang == 'de' else 'Please fill all fields', 'error')
                return redirect(url_for('admin.add_question'))
            
            # Create question
            frage = Frage(
                lernfeld_id=lernfeld_id,
                typ=Fragetyp[typ],
                schwierigkeit=Schwierigkeit[schwierigkeit],
                frage_text_de=frage_text_de,
                frage_text_en=frage_text_en,
                zeitlimit_sek=zeitlimit_sek
            )
            db.session.add(frage)
            db.session.flush()
            
            # Handle answers based on type
            if typ == 'MC':
                # Multiple choice answers
                for i in range(1, 5):  # Up to 4 answers
                    antwort_de = request.form.get(f'antwort_{i}_de', '').strip()
                    antwort_en = request.form.get(f'antwort_{i}_en', '').strip()
                    ist_korrekt = request.form.get(f'ist_korrekt_{i}') == 'on'
                    
                    if antwort_de and antwort_en:
                        antwort = Antwort(
                            frage_id=frage.id,
                            antwort_text_de=antwort_de,
                            antwort_text_en=antwort_en,
                            ist_korrekt=ist_korrekt
                        )
                        db.session.add(antwort)
            
            elif typ == 'TEXT':
                # Text answer keywords
                schluesselwoerter_de = request.form.get('schluesselwoerter_de', '').strip()
                schluesselwoerter_en = request.form.get('schluesselwoerter_en', '').strip()
                mindest_uebereinstimmung = request.form.get('mindest_uebereinstimmung', 0.9, type=float)
                
                # Split by comma or newline
                for keyword in schluesselwoerter_de.replace('\n', ',').split(','):
                    keyword = keyword.strip()
                    if keyword:
                        schluessel = TextAntwortSchluessel(
                            frage_id=frage.id,
                            schluesselwort=keyword,
                            mindest_uebereinstimmung=mindest_uebereinstimmung,
                            sprache='de'
                        )
                        db.session.add(schluessel)
                
                for keyword in schluesselwoerter_en.replace('\n', ',').split(','):
                    keyword = keyword.strip()
                    if keyword:
                        schluessel = TextAntwortSchluessel(
                            frage_id=frage.id,
                            schluesselwort=keyword,
                            mindest_uebereinstimmung=mindest_uebereinstimmung,
                            sprache='en'
                        )
                        db.session.add(schluessel)
            
            db.session.commit()
            logger.info(f"Question added: {frage.id}")
            flash('Frage erfolgreich hinzugefügt' if lang == 'de' else 'Question added successfully', 'success')
            return redirect(url_for('admin.questions'))
        
        except Exception as e:
            logger.error(f"Error adding question: {e}")
            db.session.rollback()
            flash('Fehler beim Hinzufügen der Frage' if lang == 'de' else 'Error adding question', 'error')
    
    lernfelder = Lernfeld.query.all()
    
    return render_template(
        'admin/add_question.html',
        lernfelder=lernfelder,
        fragetypen=Fragetyp,
        schwierigkeiten=Schwierigkeit,
        user=user,
        lang=lang
    )

@admin_bp.route('/questions/edit/<int:frage_id>', methods=['GET', 'POST'])
def edit_question(frage_id):
    """Edit existing question"""
    if not is_admin():
        flash('Zugriff verweigert', 'error')
        return redirect(url_for('main.index'))
    
    frage = Frage.query.get_or_404(frage_id)
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    if request.method == 'POST':
        try:
            # Update question
            frage.frage_text_de = request.form.get('frage_text_de', '').strip()
            frage.frage_text_en = request.form.get('frage_text_en', '').strip()
            frage.zeitlimit_sek = request.form.get('zeitlimit_sek', 30, type=int)
            frage.schwierigkeit = Schwierigkeit[request.form.get('schwierigkeit')]
            
            db.session.commit()
            logger.info(f"Question updated: {frage_id}")
            flash('Frage aktualisiert' if lang == 'de' else 'Question updated', 'success')
            return redirect(url_for('admin.questions'))
        
        except Exception as e:
            logger.error(f"Error updating question: {e}")
            db.session.rollback()
            flash('Fehler beim Aktualisieren' if lang == 'de' else 'Error updating', 'error')
    
    lernfelder = Lernfeld.query.all()
    
    return render_template(
        'admin/edit_question.html',
        frage=frage,
        lernfelder=lernfelder,
        schwierigkeiten=Schwierigkeit,
        user=user,
        lang=lang
    )

@admin_bp.route('/questions/delete/<int:frage_id>', methods=['POST'])
def delete_question(frage_id):
    """Delete question"""
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        frage = Frage.query.get_or_404(frage_id)
        db.session.delete(frage)
        db.session.commit()
        logger.info(f"Question deleted: {frage_id}")
        flash('Frage gelöscht', 'success')
        return redirect(url_for('admin.questions'))
    
    except Exception as e:
        logger.error(f"Error deleting question: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users')
def users():
    """Manage users"""
    if not is_admin():
        flash('Zugriff verweigert', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    # Get all users with stats
    all_users = User.query.order_by(User.fisi_punkte.desc()).all()
    
    return render_template(
        'admin/users.html',
        all_users=all_users,
        user=user,
        lang=lang
    )

@admin_bp.route('/games')
def games():
    """Manage games"""
    if not is_admin():
        flash('Zugriff verweigert', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    # Get all games
    all_games = (
        SpielSitzung.query
        .order_by(SpielSitzung.created_at.desc())
        .all()
    )
    
    return render_template(
        'admin/games.html',
        all_games=all_games,
        user=user,
        lang=lang
    )
