# views/profile_routes.py - User profile and avatar customization routes

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import User, AvatarPart
from extensions import db
import logging

logger = logging.getLogger(__name__)

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
def index():
    """User profile overview"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    # Get user's achievements
    from models import AchievementStatus
    unlocked_achievements = (
        user.achievements
        .filter_by(is_unlocked=True)
        .order_by(AchievementStatus.erreicht_am.desc())
        .all()
    )
    
    # Get user's game history
    from models import SpielTeilnahme, SpielSitzung
    recent_games = (
        db.session.query(SpielSitzung, SpielTeilnahme)
        .join(SpielTeilnahme, SpielSitzung.id == SpielTeilnahme.sitzung_id)
        .filter(SpielTeilnahme.user_id == user.id)
        .order_by(SpielSitzung.created_at.desc())
        .limit(10)
        .all()
    )
    
    return render_template(
        'profile/index.html',
        user=user,
        unlocked_achievements=unlocked_achievements,
        recent_games=recent_games,
        lang=lang
    )

@profile_bp.route('/avatar', methods=['GET', 'POST'])
def avatar():
    """Avatar customizer"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    if request.method == 'POST':
        try:
            # Get selected avatar parts
            kopf_id = request.form.get('kopf_id', type=int)
            brille_id = request.form.get('brille_id', type=int)
            farbe_id = request.form.get('farbe_id', type=int)
            
            # Update user avatar
            if kopf_id:
                user.avatar_kopf_id = kopf_id
            if brille_id:
                user.avatar_brille_id = brille_id
            if farbe_id:
                user.avatar_farbe_id = farbe_id
            
            db.session.commit()
            logger.info(f"Avatar updated for user {user.id}")
            flash('Avatar gespeichert!' if lang == 'de' else 'Avatar saved!', 'success')
            return redirect(url_for('profile.avatar'))
        
        except Exception as e:
            logger.error(f"Error updating avatar: {e}")
            db.session.rollback()
            flash('Fehler beim Speichern' if lang == 'de' else 'Error saving', 'error')
    
    # Get all avatar parts grouped by type
    koepfe = AvatarPart.query.filter_by(typ='Kopf').all()
    brillen = AvatarPart.query.filter_by(typ='Brille').all()
    farben = AvatarPart.query.filter_by(typ='Farbe').all()
    
    return render_template(
        'profile/avatar.html',
        user=user,
        koepfe=koepfe,
        brillen=brillen,
        farben=farben,
        lang=lang
    )

@profile_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """User settings"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    if request.method == 'POST':
        try:
            # Update settings
            new_lang = request.form.get('sprache')
            theme = request.form.get('theme_preference')
            
            if new_lang in ['de', 'en']:
                user.sprache = new_lang
                session['lang'] = new_lang
            
            if theme:
                user.theme_preference = theme
            
            db.session.commit()
            logger.info(f"Settings updated for user {user.id}")
            flash('Einstellungen gespeichert' if lang == 'de' else 'Settings saved', 'success')
            return redirect(url_for('profile.settings'))
        
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            db.session.rollback()
            flash('Fehler beim Speichern' if lang == 'de' else 'Error saving', 'error')
    
    return render_template(
        'profile/settings.html',
        user=user,
        lang=lang
    )

@profile_bp.route('/stats')
def stats():
    """Detailed user statistics"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    # Calculate detailed stats
    from models import SpielTeilnahme, SpielSitzung, Spielmodus
    
    # Games by mode
    games_by_mode = {}
    for mode in Spielmodus:
        count = (
            db.session.query(SpielTeilnahme)
            .join(SpielSitzung)
            .filter(
                SpielTeilnahme.user_id == user.id,
                SpielSitzung.modus == mode
            )
            .count()
        )
        games_by_mode[mode.value] = count
    
    # Total points earned
    total_points = (
        db.session.query(db.func.sum(SpielTeilnahme.punkte_multiplayer_gesamt))
        .filter(SpielTeilnahme.user_id == user.id)
        .scalar() or 0
    )
    
    # Average score per game
    avg_score = (
        db.session.query(db.func.avg(SpielTeilnahme.aktueller_punktestand))
        .filter(SpielTeilnahme.user_id == user.id)
        .scalar() or 0
    )
    
    stats = {
        'games_by_mode': games_by_mode,
        'total_points': total_points,
        'avg_score': round(avg_score, 2),
        'accuracy': user.accuracy,
        'current_streak': user.current_streak,
        'best_streak': user.best_streak
    }
    
    return render_template(
        'profile/stats.html',
        user=user,
        stats=stats,
        lang=lang
    )
