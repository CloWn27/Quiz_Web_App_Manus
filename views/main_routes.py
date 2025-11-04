# views/main_routes.py - Main application routes

from flask import Blueprint, render_template, session, redirect, url_for, request
from models import User, Lernfeld, SpielSitzung, Achievement
from extensions import db
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page with cyberpunk intro and language selection"""
    lang = session.get('lang', 'de')
    return render_template('index.html', lang=lang)

@main_bp.route('/set_language/<lang_code>')
def set_language(lang_code):
    """Set user language preference"""
    if lang_code in ['de', 'en']:
        session['lang'] = lang_code
        session.permanent = True
        
        # Update user preference if logged in
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                user.sprache = lang_code
                db.session.commit()
        
        logger.info(f"Language set to: {lang_code}")
    
    # Redirect back to referrer or home
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/dashboard')
def dashboard():
    """Main dashboard after login"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    lang = session.get('lang', user.sprache)
    
    # Get user stats
    stats = {
        'fisi_punkte': user.fisi_punkte,
        'games_played': user.games_played,
        'accuracy': user.accuracy,
        'current_streak': user.current_streak,
        'best_streak': user.best_streak
    }
    
    # Get available Lernfelder
    lernfelder = Lernfeld.query.all()
    
    # Get recent achievements
    from models import AchievementStatus
    recent_achievements = (
        db.session.query(Achievement)
        .join(AchievementStatus, Achievement.id == AchievementStatus.achievement_id)
        .filter(AchievementStatus.user_id == user.id)
        .filter(AchievementStatus.is_unlocked == True)
        .order_by(AchievementStatus.unlocked_at.desc())
        .limit(5)
        .all()
    )
    
    return render_template(
        'dashboard.html',
        user=user,
        stats=stats,
        lernfelder=lernfelder,
        recent_achievements=recent_achievements,
        lang=lang
    )

@main_bp.route('/leaderboard')
def leaderboard():
    """Display top players leaderboard"""
    lang = session.get('lang', 'de')
    
    # Get top 10 players by FiSi-Punkte
    top_players = (
        User.query
        .filter(User.fisi_punkte > 0)
        .order_by(User.fisi_punkte.desc())
        .limit(10)
        .all()
    )
    
    # Get current user rank if logged in
    current_user_rank = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.fisi_punkte > 0:
            # Calculate rank
            higher_ranked = User.query.filter(User.fisi_punkte > user.fisi_punkte).count()
            current_user_rank = higher_ranked + 1
    
    return render_template(
        'leaderboard.html',
        top_players=top_players,
        current_user_rank=current_user_rank,
        lang=lang
    )

@main_bp.route('/achievements')
def achievements():
    """Display all achievements and user progress"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    lang = session.get('lang', user.sprache)
    
    # Get all achievements grouped by category
    all_achievements = Achievement.query.filter_by(is_active=True).all()
    
    # Group by category
    achievements_by_category = {}
    for achievement in all_achievements:
        if achievement.category not in achievements_by_category:
            achievements_by_category[achievement.category] = []
        achievements_by_category[achievement.category].append(achievement)
    
    # Get user's achievement status
    from models import AchievementStatus
    user_achievement_status = {
        status.achievement_id: status
        for status in user.achievements.all()
    }
    
    return render_template(
        'achievements.html',
        achievements_by_category=achievements_by_category,
        user_achievement_status=user_achievement_status,
        user=user,
        lang=lang
    )

@main_bp.route('/about')
def about():
    """About page"""
    lang = session.get('lang', 'de')
    return render_template('about.html', lang=lang)

@main_bp.route('/help')
def help():
    """Help/FAQ page"""
    lang = session.get('lang', 'de')
    return render_template('help.html', lang=lang)
