# socketio_events.py - Real-time SocketIO event handlers

from flask import session, request
from flask_socketio import emit, join_room, leave_room, rooms
from extensions import socketio, db
from models import (
    SpielSitzung, SpielTeilnahme, User, Frage, Antwort,
    TextAntwortSchluessel, Fragetyp, Achievement, AchievementStatus
)
from datetime import datetime, timezone
import logging
import random
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Store active connections
active_connections = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    user_id = session.get('user_id')
    if user_id:
        active_connections[request.sid] = user_id
        logger.info(f"User {user_id} connected (sid: {request.sid})")
        emit('connected', {'status': 'success'})
    else:
        logger.warning(f"Unauthorized connection attempt (sid: {request.sid})")
        emit('error', {'message': 'Not authenticated'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user_id = active_connections.pop(request.sid, None)
    if user_id:
        logger.info(f"User {user_id} disconnected (sid: {request.sid})")

@socketio.on('join_game')
def handle_join_game(data):
    """Player joins a game room"""
    user_id = session.get('user_id')
    room_code = data.get('room_code')
    
    if not user_id or not room_code:
        emit('error', {'message': 'Invalid request'})
        return
    
    # Get game session
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    user = User.query.get(user_id)
    
    if not sitzung or not user:
        emit('error', {'message': 'Game or user not found'})
        return
    
    # Join SocketIO room
    join_room(room_code)
    logger.info(f"User {user.username} joined room {room_code}")
    
    # Get or create participation
    teilnahme = SpielTeilnahme.query.filter_by(
        sitzung_id=sitzung.id,
        user_id=user.id
    ).first()
    
    if not teilnahme:
        teilnahme = SpielTeilnahme(
            sitzung_id=sitzung.id,
            user_id=user.id
        )
        db.session.add(teilnahme)
        db.session.commit()
    
    # Broadcast player joined to all in room
    emit('player_joined', {
        'user_id': user.id,
        'username': user.username,
        'player_count': sitzung.teilnahmen.count()
    }, room=room_code)
    
    # Send current lobby state to joining player
    teilnehmer_list = []
    for t in sitzung.teilnahmen:
        teilnehmer_list.append({
            'user_id': t.spieler.id,
            'username': t.spieler.username,
            'score': t.aktueller_punktestand
        })
    
    emit('update_lobby', {
        'room_code': room_code,
        'modus': sitzung.modus.value,
        'schwierigkeit': sitzung.schwierigkeit_level.value,
        'lernfeld': sitzung.lernfeld.get_name(session.get('lang', 'de')),
        'teilnehmer': teilnehmer_list,
        'is_active': sitzung.ist_aktiv
    })

@socketio.on('leave_game')
def handle_leave_game(data):
    """Player leaves a game room"""
    user_id = session.get('user_id')
    room_code = data.get('room_code')
    
    if room_code:
        leave_room(room_code)
        user = User.query.get(user_id)
        logger.info(f"User {user.username if user else user_id} left room {room_code}")
        
        # Broadcast player left
        emit('player_left', {
            'user_id': user_id,
            'username': user.username if user else 'Unknown'
        }, room=room_code)

@socketio.on('start_game')
def handle_start_game(data):
    """Host starts the game"""
    user_id = session.get('user_id')
    room_code = data.get('room_code')
    
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    
    if not sitzung or sitzung.ersteller_id != user_id:
        emit('error', {'message': 'Unauthorized or game not found'})
        return
    
    # Update game state
    sitzung.started_at = datetime.now(timezone.utc)
    sitzung.aktueller_frage_index = 0
    db.session.commit()
    
    logger.info(f"Game {room_code} started by user {user_id}")
    
    # Broadcast game started
    emit('game_started', {
        'room_code': room_code,
        'message': 'Spiel startet!' if session.get('lang', 'de') == 'de' else 'Game starting!'
    }, room=room_code)
    
    # Send first question after a short delay
    socketio.sleep(2)
    send_next_question(room_code)

def send_next_question(room_code):
    """Send the next question to all players"""
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    if not sitzung:
        return
    
    # Get questions for this game
    fragen = Frage.query.filter_by(
        lernfeld_id=sitzung.lernfeld_id,
        schwierigkeit=sitzung.schwierigkeit_level
    ).all()
    
    if not fragen:
        # No more questions, end game
        end_game(room_code)
        return
    
    # Select random question if not already selected
    if sitzung.aktueller_frage_index >= len(fragen):
        end_game(room_code)
        return
    
    # Get random question
    frage = random.choice(fragen)
    sitzung.aktueller_frage_index += 1
    db.session.commit()
    
    lang = session.get('lang', 'de')
    
    # Prepare question data
    question_data = {
        'frage_id': frage.id,
        'frage_text': frage.get_text(lang),
        'typ': frage.typ.value,
        'zeitlimit_sek': frage.zeitlimit_sek,
        'frage_nummer': sitzung.aktueller_frage_index,
        'punkte': frage.get_points()
    }
    
    # Add answers for MC questions
    if frage.typ == Fragetyp.MC:
        antworten = []
        for antwort in frage.antworten:
            antworten.append({
                'id': antwort.id,
                'text': antwort.get_text(lang)
            })
        random.shuffle(antworten)  # Randomize answer order
        question_data['antworten'] = antworten
    
    logger.info(f"Sending question {frage.id} to room {room_code}")
    
    # Broadcast question to all players
    socketio.emit('new_question', question_data, room=room_code)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Player submits an answer"""
    user_id = session.get('user_id')
    room_code = data.get('room_code')
    frage_id = data.get('frage_id')
    answer = data.get('answer')  # Can be answer_id (MC) or text (TEXT)
    time_elapsed = data.get('time_elapsed', 0)
    
    if not all([user_id, room_code, frage_id]):
        emit('error', {'message': 'Invalid request'})
        return
    
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    teilnahme = SpielTeilnahme.query.filter_by(
        sitzung_id=sitzung.id,
        user_id=user_id
    ).first()
    frage = Frage.query.get(frage_id)
    
    if not all([sitzung, teilnahme, frage]):
        emit('error', {'message': 'Data not found'})
        return
    
    # Check if player already answered this question
    answers_data = teilnahme.answers_data or []
    if any(a.get('frage_id') == frage_id for a in answers_data):
        emit('error', {'message': 'Already answered'})
        return
    
    # Validate answer
    is_correct = False
    correct_answer = None
    
    if frage.typ == Fragetyp.MC:
        # Multiple choice validation
        if isinstance(answer, list):
            # Multiple correct answers possible
            correct_ids = [a.id for a in frage.antworten if a.ist_korrekt]
            is_correct = set(answer) == set(correct_ids)
        else:
            # Single answer
            antwort = Antwort.query.get(answer)
            is_correct = antwort and antwort.ist_korrekt
        
        correct_answer = [a.id for a in frage.antworten if a.ist_korrekt]
    
    elif frage.typ == Fragetyp.TEXT:
        # Text answer validation with fuzzy matching
        lang = session.get('lang', 'de')
        schluessel = TextAntwortSchluessel.query.filter_by(
            frage_id=frage_id,
            sprache=lang
        ).all()
        
        answer_text = str(answer).strip().lower()
        for sk in schluessel:
            similarity = SequenceMatcher(None, answer_text, sk.schluesselwort.lower()).ratio()
            if similarity >= sk.mindest_uebereinstimmung:
                is_correct = True
                correct_answer = sk.schluesselwort
                break
        
        if not is_correct and schluessel:
            correct_answer = schluessel[0].schluesselwort
    
    # Calculate points
    points_earned = 0
    if is_correct:
        base_points = frage.get_points()
        # Time bonus: faster answers get more points
        time_bonus = max(0, 1 - (time_elapsed / frage.zeitlimit_sek)) * 0.5
        points_earned = int(base_points * (1 + time_bonus))
        
        # Update teilnahme
        teilnahme.aktueller_punktestand += points_earned
        teilnahme.punkte_multiplayer_gesamt += points_earned
        
        # Update user stats
        user = User.query.get(user_id)
        user.correct_answers += 1
        user.current_streak += 1
        if user.current_streak > user.best_streak:
            user.best_streak = user.current_streak
        user.fisi_punkte += points_earned
    else:
        # Wrong answer
        user = User.query.get(user_id)
        user.current_streak = 0
        
        # Survival mode logic
        if sitzung.modus.value in ['Survival_Normal', 'Survival_Hardcore']:
            teilnahme.hat_ueberlebt = False
            teilnahme.ausgeschieden_bei_frage = sitzung.aktueller_frage_index
    
    # Update user stats
    user.questions_answered += 1
    
    # Store answer in history
    answers_data.append({
        'frage_id': frage_id,
        'answer': answer,
        'is_correct': is_correct,
        'points_earned': points_earned,
        'time_elapsed': time_elapsed
    })
    teilnahme.answers_data = answers_data
    
    db.session.commit()
    
    logger.info(f"User {user_id} answered question {frage_id}: {'correct' if is_correct else 'wrong'}")
    
    # Send result to player
    emit('answer_result', {
        'is_correct': is_correct,
        'points_earned': points_earned,
        'correct_answer': correct_answer,
        'total_score': teilnahme.aktueller_punktestand
    })
    
    # Broadcast score update to room
    socketio.emit('score_update', {
        'user_id': user_id,
        'username': user.username,
        'score': teilnahme.aktueller_punktestand,
        'points_change': points_earned
    }, room=room_code)
    
    # Check if all players answered
    check_all_answered(room_code, frage_id)

def check_all_answered(room_code, frage_id):
    """Check if all players have answered the current question"""
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    if not sitzung:
        return
    
    # Count answers for this question
    answered_count = 0
    total_players = sitzung.teilnahmen.count()
    
    for teilnahme in sitzung.teilnahmen:
        answers_data = teilnahme.answers_data or []
        if any(a.get('frage_id') == frage_id for a in answers_data):
            answered_count += 1
    
    # If all answered, proceed to next question
    if answered_count >= total_players:
        logger.info(f"All players answered in room {room_code}, proceeding to next question")
        socketio.sleep(3)  # Short delay to show results
        send_next_question(room_code)

@socketio.on('next_question')
def handle_next_question(data):
    """Host triggers next question"""
    user_id = session.get('user_id')
    room_code = data.get('room_code')
    
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    
    if not sitzung or sitzung.ersteller_id != user_id:
        emit('error', {'message': 'Unauthorized'})
        return
    
    send_next_question(room_code)

def end_game(room_code):
    """End the game and show results"""
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    if not sitzung:
        return
    
    sitzung.ist_aktiv = False
    sitzung.ended_at = datetime.now(timezone.utc)
    
    # Update user stats
    for teilnahme in sitzung.teilnahmen:
        user = User.query.get(teilnahme.user_id)
        user.games_played += 1
    
    db.session.commit()
    
    # Prepare final results
    results = []
    for teilnahme in sitzung.teilnahmen.order_by(SpielTeilnahme.aktueller_punktestand.desc()):
        results.append({
            'user_id': teilnahme.user_id,
            'username': teilnahme.spieler.username,
            'score': teilnahme.aktueller_punktestand,
            'hat_ueberlebt': teilnahme.hat_ueberlebt
        })
    
    logger.info(f"Game {room_code} ended")
    
    # Broadcast game over
    socketio.emit('game_over', {
        'results': results,
        'winner': results[0] if results else None
    }, room=room_code)
    
    # Check and award achievements
    check_achievements(room_code)

def check_achievements(room_code):
    """Check and award achievements for players"""
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    if not sitzung:
        return
    
    for teilnahme in sitzung.teilnahmen:
        user = User.query.get(teilnahme.user_id)
        
        # Check various achievement conditions
        achievements_to_award = []
        
        # First Win
        if user.games_played == 1:
            ach = Achievement.query.filter_by(schluessel='FIRST_WIN').first()
            if ach:
                achievements_to_award.append(ach)
        
        # Streak achievements
        if user.current_streak >= 5:
            ach = Achievement.query.filter_by(schluessel='STREAK_5').first()
            if ach:
                achievements_to_award.append(ach)
        
        if user.current_streak >= 10:
            ach = Achievement.query.filter_by(schluessel='STREAK_10').first()
            if ach:
                achievements_to_award.append(ach)
        
        # Perfect game
        if user.accuracy == 100 and user.questions_answered > 0:
            ach = Achievement.query.filter_by(schluessel='PERFECT_GAME').first()
            if ach:
                achievements_to_award.append(ach)
        
        # Award achievements
        for ach in achievements_to_award:
            # Check if already unlocked
            status = AchievementStatus.query.filter_by(
                user_id=user.id,
                achievement_id=ach.id
            ).first()
            
            if not status:
                status = AchievementStatus(
                    user_id=user.id,
                    achievement_id=ach.id,
                    is_unlocked=True,
                    erreicht_am=datetime.now(timezone.utc)
                )
                db.session.add(status)
                
                # Notify player
                socketio.emit('achievement_unlocked', {
                    'achievement': {
                        'titel': ach.get_titel(session.get('lang', 'de')),
                        'icon': ach.icon,
                        'points': ach.points
                    }
                }, room=request.sid)
        
        db.session.commit()

@socketio.on('kick_player')
def handle_kick_player(data):
    """Host kicks a player from the game"""
    user_id = session.get('user_id')
    room_code = data.get('room_code')
    player_id = data.get('player_id')
    
    sitzung = SpielSitzung.query.filter_by(raum_code=room_code).first()
    
    if not sitzung or sitzung.ersteller_id != user_id:
        emit('error', {'message': 'Unauthorized'})
        return
    
    # Mark player as kicked
    teilnahme = SpielTeilnahme.query.filter_by(
        sitzung_id=sitzung.id,
        user_id=player_id
    ).first()
    
    if teilnahme:
        teilnahme.hat_ueberlebt = False
        db.session.commit()
        
        # Notify kicked player
        socketio.emit('kicked_out', {
            'message': 'Du wurdest aus dem Spiel entfernt'
        }, room=room_code, skip_sid=request.sid)
        
        logger.info(f"Player {player_id} kicked from room {room_code}")
