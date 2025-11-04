# models.py - Enhanced Database Models for FiSi-Quiz-Cyberpunk

from datetime import datetime, timezone
from sqlalchemy import JSON, Enum as SQLEnum
from extensions import db
import enum

# Enums für Typsicherheit
class Fragetyp(enum.Enum):
    """Question types"""
    MC = "Multiple Choice"
    TEXT = "Textantwort"

class Schwierigkeit(enum.Enum):
    """Difficulty levels"""
    LEICHT = "Leicht"
    MITTEL = "Mittel"
    SCHWER = "Schwer"
    HEAVY = "Heavy"

class Spielmodus(enum.Enum):
    """Game modes"""
    KLASSISCH = "Klassisch"
    SURVIVAL_NORMAL = "Survival_Normal"
    SURVIVAL_HARDCORE = "Survival_Hardcore"
    SOLO = "Solo"

class User(db.Model):
    """Enhanced User model with avatar customization and stats"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    
    # FiSi-Punkte für Bestenliste
    fisi_punkte = db.Column(db.Integer, default=0)
    
    # Avatar-Beziehungen
    avatar_kopf_id = db.Column(db.Integer, db.ForeignKey('avatar_part.id'), nullable=True)
    avatar_brille_id = db.Column(db.Integer, db.ForeignKey('avatar_part.id'), nullable=True)
    avatar_farbe_id = db.Column(db.Integer, db.ForeignKey('avatar_part.id'), nullable=True)
    
    # Preferences
    sprache = db.Column(db.String(5), default='de')  # 'de' oder 'en'
    theme_preference = db.Column(db.String(10), default='cyberpunk')
    
    # Stats
    games_played = db.Column(db.Integer, default=0)
    questions_answered = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
    
    # Timestamps
    registriert_am = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_active = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    teilnahmen = db.relationship('SpielTeilnahme', backref='spieler', lazy='dynamic', cascade='all, delete-orphan')
    achievements = db.relationship('AchievementStatus', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def accuracy(self):
        """Calculate answer accuracy percentage"""
        if self.questions_answered == 0:
            return 0
        return round((self.correct_answers / self.questions_answered) * 100, 2)

class AvatarPart(db.Model):
    """Avatar customization parts (Kopf, Brille, Farbe)"""
    __tablename__ = 'avatar_part'
    
    id = db.Column(db.Integer, primary_key=True)
    typ = db.Column(db.String(20), nullable=False)  # 'Kopf', 'Brille', 'Farbe'
    bezeichnung = db.Column(db.String(80), nullable=False)
    css_klasse = db.Column(db.String(100), nullable=False)  # Tailwind oder Custom-Klasse
    preis = db.Column(db.Integer, default=0)  # Für zukünftiges Währungssystem
    
    def __repr__(self):
        return f'<AvatarPart {self.typ}: {self.bezeichnung}>'

class Lernfeld(db.Model):
    """Learning field categories (e.g., Lernfeld 5: Vernetzte Systeme)"""
    __tablename__ = 'lernfeld'
    
    id = db.Column(db.Integer, primary_key=True)
    name_de = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    beschreibung_de = db.Column(db.Text)
    beschreibung_en = db.Column(db.Text)
    
    # Relationships
    fragen = db.relationship('Frage', backref='lernfeld', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Lernfeld {self.name_de}>'
    
    def get_name(self, lang='de'):
        """Get name in specified language"""
        return self.name_de if lang == 'de' else self.name_en

class Frage(db.Model):
    """Question model with i18n support"""
    __tablename__ = 'frage'
    
    id = db.Column(db.Integer, primary_key=True)
    lernfeld_id = db.Column(db.Integer, db.ForeignKey('lernfeld.id'), nullable=False)
    
    typ = db.Column(SQLEnum(Fragetyp), nullable=False)
    schwierigkeit = db.Column(SQLEnum(Schwierigkeit), nullable=False)
    
    # Multilingual question text
    frage_text_de = db.Column(db.Text, nullable=False)
    frage_text_en = db.Column(db.Text, nullable=False)
    
    zeitlimit_sek = db.Column(db.Integer, default=30)
    
    # Relationships
    antworten = db.relationship('Antwort', backref='frage', lazy='dynamic', cascade='all, delete-orphan')
    text_schluessel = db.relationship('TextAntwortSchluessel', backref='frage', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Frage {self.id}: {self.frage_text_de[:50]}...>'
    
    def get_text(self, lang='de'):
        """Get question text in specified language"""
        return self.frage_text_de if lang == 'de' else self.frage_text_en
    
    def get_points(self):
        """Calculate base points based on difficulty"""
        points_map = {
            Schwierigkeit.LEICHT: 100,
            Schwierigkeit.MITTEL: 200,
            Schwierigkeit.SCHWER: 300,
            Schwierigkeit.HEAVY: 500
        }
        return points_map.get(self.schwierigkeit, 100)

class Antwort(db.Model):
    """Multiple choice answer options"""
    __tablename__ = 'antwort'
    
    id = db.Column(db.Integer, primary_key=True)
    frage_id = db.Column(db.Integer, db.ForeignKey('frage.id'), nullable=False)
    
    # Multilingual answer text
    antwort_text_de = db.Column(db.String(255), nullable=False)
    antwort_text_en = db.Column(db.String(255), nullable=False)
    
    ist_korrekt = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Antwort {self.id}: {self.antwort_text_de[:30]}...>'
    
    def get_text(self, lang='de'):
        """Get answer text in specified language"""
        return self.antwort_text_de if lang == 'de' else self.antwort_text_en

class TextAntwortSchluessel(db.Model):
    """Text answer validation keywords with fuzzy matching support"""
    __tablename__ = 'text_antwort_schluessel'
    
    id = db.Column(db.Integer, primary_key=True)
    frage_id = db.Column(db.Integer, db.ForeignKey('frage.id'), nullable=False)
    
    schluesselwort = db.Column(db.String(100), nullable=False)
    mindest_uebereinstimmung = db.Column(db.Float, default=0.9)  # Für fuzzy matching
    sprache = db.Column(db.String(5), nullable=False)  # 'de' oder 'en'
    
    def __repr__(self):
        return f'<TextSchluessel {self.schluesselwort}>'

class SpielSitzung(db.Model):
    """Game session (like Kahoot room)"""
    __tablename__ = 'spiel_sitzung'
    
    id = db.Column(db.Integer, primary_key=True)
    raum_code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    
    modus = db.Column(SQLEnum(Spielmodus), nullable=False)
    schwierigkeit_level = db.Column(SQLEnum(Schwierigkeit), nullable=False)
    
    aktueller_frage_index = db.Column(db.Integer, default=0)
    ist_aktiv = db.Column(db.Boolean, default=True)
    
    lernfeld_id = db.Column(db.Integer, db.ForeignKey('lernfeld.id'), nullable=False)
    ersteller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # UI customization
    musik_thema = db.Column(db.String(50), default='Cyber-Dystopia')
    design_thema = db.Column(db.String(50), default='Neon-Matrix')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    teilnahmen = db.relationship('SpielTeilnahme', backref='sitzung', lazy='dynamic', cascade='all, delete-orphan')
    lernfeld = db.relationship('Lernfeld', backref='sitzungen')
    ersteller = db.relationship('User', backref='erstellte_spiele', foreign_keys=[ersteller_id])
    
    def __repr__(self):
        return f'<SpielSitzung {self.raum_code}: {self.modus.value}>'

class SpielTeilnahme(db.Model):
    """Player participation in a game session"""
    __tablename__ = 'spiel_teilnahme'
    
    id = db.Column(db.Integer, primary_key=True)
    sitzung_id = db.Column(db.Integer, db.ForeignKey('spiel_sitzung.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    aktueller_punktestand = db.Column(db.Integer, default=0)
    punkte_multiplayer_gesamt = db.Column(db.Integer, default=0)
    
    # Für Survival-Modi
    hat_ueberlebt = db.Column(db.Boolean, default=True)
    ausgeschieden_bei_frage = db.Column(db.Integer, default=0)  # 0 = Nicht ausgeschieden
    
    # Answer tracking
    answers_data = db.Column(JSON, default=list)  # Store answer history
    
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('sitzung_id', 'user_id', name='_user_sitzung_uc'),)
    
    def __repr__(self):
        return f'<SpielTeilnahme User:{self.user_id} Sitzung:{self.sitzung_id}>'

class Achievement(db.Model):
    """Achievement definitions"""
    __tablename__ = 'achievement'
    
    id = db.Column(db.Integer, primary_key=True)
    schluessel = db.Column(db.String(50), unique=True, nullable=False)  # z.B. 'FIRST_WIN'
    
    # Multilingual titles and descriptions
    titel_de = db.Column(db.String(100), nullable=False)
    titel_en = db.Column(db.String(100), nullable=False)
    beschreibung_de = db.Column(db.Text)
    beschreibung_en = db.Column(db.Text)
    
    icon = db.Column(db.String(50), default='🏆')
    category = db.Column(db.String(50), nullable=False)  # 'score', 'streak', 'games'
    requirement_type = db.Column(db.String(20), nullable=False)  # 'count', 'streak', 'percentage'
    requirement_value = db.Column(db.Integer, nullable=False)
    
    points = db.Column(db.Integer, default=10)
    rarity = db.Column(db.String(10), default='common')  # common, rare, epic, legendary
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Achievement {self.schluessel}>'
    
    def get_titel(self, lang='de'):
        """Get title in specified language"""
        return self.titel_de if lang == 'de' else self.titel_en

class AchievementStatus(db.Model):
    """User achievement progress and unlocks"""
    __tablename__ = 'achievement_status'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    
    progress = db.Column(db.Integer, default=0)
    is_unlocked = db.Column(db.Boolean, default=False)
    erreicht_am = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    achievement = db.relationship('Achievement', backref='user_achievements')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id', name='_user_achievement_uc'),)
    
    def __repr__(self):
        return f'<AchievementStatus User:{self.user_id} Achievement:{self.achievement_id}>'

# Legacy models for compatibility with existing flask-quiz-app
class Game(db.Model):
    """Legacy game model for backward compatibility"""
    __tablename__ = 'games'
    
    pin = db.Column(db.String(6), primary_key=True)
    host_name = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(20), default='waiting')
    current_question = db.Column(db.Integer, default=0)
    questions = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    players = db.relationship('Player', backref='game', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Game {self.pin}>'

class Player(db.Model):
    """Legacy player model for backward compatibility"""
    __tablename__ = 'players'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    game_pin = db.Column(db.String(6), db.ForeignKey('games.pin'), nullable=False)
    score = db.Column(db.Integer, default=0)
    answers = db.Column(JSON, default=list)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Player {self.name}>'
