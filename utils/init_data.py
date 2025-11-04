# utils/init_data.py - Initialize default database content

from extensions import db
from models import (
    Lernfeld, Frage, Antwort, TextAntwortSchluessel,
    Fragetyp, Schwierigkeit, Achievement, AvatarPart
)
import logging

logger = logging.getLogger(__name__)

def initialize_default_data():
    """Initialize default data for the application"""
    try:
        # Initialize Lernfelder
        if Lernfeld.query.count() == 0:
            logger.info("Initializing Lernfelder...")
            initialize_lernfelder()
        
        # Initialize sample questions for Lernfeld 5
        if Frage.query.count() == 0:
            logger.info("Initializing sample questions...")
            initialize_sample_questions()
        
        # Initialize achievements
        if Achievement.query.count() == 0:
            logger.info("Initializing achievements...")
            initialize_achievements()
        
        # Initialize avatar parts
        if AvatarPart.query.count() == 0:
            logger.info("Initializing avatar parts...")
            initialize_avatar_parts()
        
        db.session.commit()
        logger.info("Default data initialization completed")
        
    except Exception as e:
        logger.error(f"Error initializing default data: {e}")
        db.session.rollback()

def initialize_lernfelder():
    """Initialize learning fields"""
    lernfelder = [
        {
            'name_de': 'Lernfeld 1: Betrieb und sein Umfeld',
            'name_en': 'Subject 1: Company and its Environment',
            'beschreibung_de': 'Grundlagen der Betriebswirtschaft',
            'beschreibung_en': 'Business administration basics'
        },
        {
            'name_de': 'Lernfeld 2: Geschäftsprozesse und betriebliche Organisation',
            'name_en': 'Subject 2: Business Processes and Organization',
            'beschreibung_de': 'Prozessmanagement und Organisation',
            'beschreibung_en': 'Process management and organization'
        },
        {
            'name_de': 'Lernfeld 3: Informationsquellen und Arbeitsmethoden',
            'name_en': 'Subject 3: Information Sources and Work Methods',
            'beschreibung_de': 'Recherche und Dokumentation',
            'beschreibung_en': 'Research and documentation'
        },
        {
            'name_de': 'Lernfeld 4: Einfache IT-Systeme',
            'name_en': 'Subject 4: Simple IT Systems',
            'beschreibung_de': 'Grundlagen der IT-Systeme',
            'beschreibung_en': 'IT systems basics'
        },
        {
            'name_de': 'Lernfeld 5: Vernetzte Systeme und Dienste',
            'name_en': 'Subject 5: Networked Systems and Services',
            'beschreibung_de': 'Netzwerktechnik und Protokolle',
            'beschreibung_en': 'Network technology and protocols'
        },
    ]
    
    for lf_data in lernfelder:
        lf = Lernfeld(**lf_data)
        db.session.add(lf)
    
    logger.info(f"Created {len(lernfelder)} Lernfelder")

def initialize_sample_questions():
    """Initialize sample questions for Lernfeld 5"""
    # Get Lernfeld 5
    lernfeld5 = Lernfeld.query.filter_by(name_de='Lernfeld 5: Vernetzte Systeme und Dienste').first()
    if not lernfeld5:
        logger.warning("Lernfeld 5 not found, skipping sample questions")
        return
    
    # Question 1: MC-Leicht
    frage1 = Frage(
        lernfeld_id=lernfeld5.id,
        typ=Fragetyp.MC,
        schwierigkeit=Schwierigkeit.LEICHT,
        frage_text_de='Welcher Port wird standardmäßig für unverschlüsselte Webseiten-Kommunikation verwendet?',
        frage_text_en='Which port is standard for unencrypted website communication?',
        zeitlimit_sek=30
    )
    db.session.add(frage1)
    db.session.flush()
    
    antworten1 = [
        Antwort(frage_id=frage1.id, antwort_text_de='21', antwort_text_en='21', ist_korrekt=False),
        Antwort(frage_id=frage1.id, antwort_text_de='80', antwort_text_en='80', ist_korrekt=True),
        Antwort(frage_id=frage1.id, antwort_text_de='443', antwort_text_en='443', ist_korrekt=False),
        Antwort(frage_id=frage1.id, antwort_text_de='23', antwort_text_en='23', ist_korrekt=False),
    ]
    for ant in antworten1:
        db.session.add(ant)
    
    # Question 2: MC-Mittel (Multiple correct answers)
    frage2 = Frage(
        lernfeld_id=lernfeld5.id,
        typ=Fragetyp.MC,
        schwierigkeit=Schwierigkeit.MITTEL,
        frage_text_de='Welche der folgenden Protokolle nutzen das User Datagram Protocol (UDP)? (Wähle zwei)',
        frage_text_en='Which of the following protocols use the User Datagram Protocol (UDP)? (Select two)',
        zeitlimit_sek=45
    )
    db.session.add(frage2)
    db.session.flush()
    
    antworten2 = [
        Antwort(frage_id=frage2.id, antwort_text_de='DNS', antwort_text_en='DNS', ist_korrekt=True),
        Antwort(frage_id=frage2.id, antwort_text_de='HTTP', antwort_text_en='HTTP', ist_korrekt=False),
        Antwort(frage_id=frage2.id, antwort_text_de='SNMP', antwort_text_en='SNMP', ist_korrekt=True),
        Antwort(frage_id=frage2.id, antwort_text_de='FTP', antwort_text_en='FTP', ist_korrekt=False),
    ]
    for ant in antworten2:
        db.session.add(ant)
    
    # Question 3: Text-Schwer
    frage3 = Frage(
        lernfeld_id=lernfeld5.id,
        typ=Fragetyp.TEXT,
        schwierigkeit=Schwierigkeit.SCHWER,
        frage_text_de='Wie lautet der vollständige Befehl in Debian/Ubuntu, um die Liste der verfügbaren Pakete zu aktualisieren?',
        frage_text_en='What is the full command in Debian/Ubuntu to update the list of available packages?',
        zeitlimit_sek=60
    )
    db.session.add(frage3)
    db.session.flush()
    
    schluessel3 = [
        TextAntwortSchluessel(frage_id=frage3.id, schluesselwort='apt update', mindest_uebereinstimmung=0.9, sprache='de'),
        TextAntwortSchluessel(frage_id=frage3.id, schluesselwort='apt-get update', mindest_uebereinstimmung=0.9, sprache='de'),
        TextAntwortSchluessel(frage_id=frage3.id, schluesselwort='apt update', mindest_uebereinstimmung=0.9, sprache='en'),
        TextAntwortSchluessel(frage_id=frage3.id, schluesselwort='apt-get update', mindest_uebereinstimmung=0.9, sprache='en'),
    ]
    for sk in schluessel3:
        db.session.add(sk)
    
    # Question 4: Text-Heavy
    frage4 = Frage(
        lernfeld_id=lernfeld5.id,
        typ=Fragetyp.TEXT,
        schwierigkeit=Schwierigkeit.HEAVY,
        frage_text_de='Ein Client meldet "Destination Host Unreachable" beim Ping. Nenne die wahrscheinlichste Ursache im Layer 3 des OSI-Modells.',
        frage_text_en='A client reports "Destination Host Unreachable" on a ping. Name the most likely cause at Layer 3 of the OSI model.',
        zeitlimit_sek=90
    )
    db.session.add(frage4)
    db.session.flush()
    
    schluessel4 = [
        TextAntwortSchluessel(frage_id=frage4.id, schluesselwort='Falsches Gateway', mindest_uebereinstimmung=0.7, sprache='de'),
        TextAntwortSchluessel(frage_id=frage4.id, schluesselwort='Fehlerhaftes Routing', mindest_uebereinstimmung=0.7, sprache='de'),
        TextAntwortSchluessel(frage_id=frage4.id, schluesselwort='Kein Route', mindest_uebereinstimmung=0.7, sprache='de'),
        TextAntwortSchluessel(frage_id=frage4.id, schluesselwort='Wrong Gateway', mindest_uebereinstimmung=0.7, sprache='en'),
        TextAntwortSchluessel(frage_id=frage4.id, schluesselwort='Faulty Routing', mindest_uebereinstimmung=0.7, sprache='en'),
        TextAntwortSchluessel(frage_id=frage4.id, schluesselwort='No Route', mindest_uebereinstimmung=0.7, sprache='en'),
    ]
    for sk in schluessel4:
        db.session.add(sk)
    
    # Question 5: MC-Heavy
    frage5 = Frage(
        lernfeld_id=lernfeld5.id,
        typ=Fragetyp.MC,
        schwierigkeit=Schwierigkeit.HEAVY,
        frage_text_de='Welche der folgenden Techniken ist die effizienteste Methode, um in einem Rechenzentrum das Broadcast-Chaos und die Kollisionsdomänen zu begrenzen?',
        frage_text_en='Which of the following techniques is the most efficient method to limit broadcast storms and collision domains in a data center?',
        zeitlimit_sek=60
    )
    db.session.add(frage5)
    db.session.flush()
    
    antworten5 = [
        Antwort(frage_id=frage5.id, antwort_text_de='Verwendung von Hubs statt Switches', antwort_text_en='Using hubs instead of switches', ist_korrekt=False),
        Antwort(frage_id=frage5.id, antwort_text_de='Implementierung von VLANs', antwort_text_en='Implementing VLANs', ist_korrekt=True),
        Antwort(frage_id=frage5.id, antwort_text_de='Erhöhen der MTU-Größe', antwort_text_en='Increasing the MTU size', ist_korrekt=False),
        Antwort(frage_id=frage5.id, antwort_text_de='Deaktivieren von Spanning Tree', antwort_text_en='Disabling Spanning Tree', ist_korrekt=False),
    ]
    for ant in antworten5:
        db.session.add(ant)
    
    logger.info("Created 5 sample questions for Lernfeld 5")

def initialize_achievements():
    """Initialize achievement definitions"""
    achievements = [
        {
            'schluessel': 'FIRST_WIN',
            'titel_de': 'Erster Sieg',
            'titel_en': 'First Victory',
            'beschreibung_de': 'Gewinne dein erstes Spiel',
            'beschreibung_en': 'Win your first game',
            'icon': '🏆',
            'category': 'games',
            'requirement_type': 'count',
            'requirement_value': 1,
            'points': 10,
            'rarity': 'common'
        },
        {
            'schluessel': 'STREAK_5',
            'titel_de': 'Fünfer-Serie',
            'titel_en': 'Five Streak',
            'beschreibung_de': 'Beantworte 5 Fragen hintereinander richtig',
            'beschreibung_en': 'Answer 5 questions correctly in a row',
            'icon': '🔥',
            'category': 'streak',
            'requirement_type': 'streak',
            'requirement_value': 5,
            'points': 20,
            'rarity': 'common'
        },
        {
            'schluessel': 'STREAK_10',
            'titel_de': 'Zehner-Serie',
            'titel_en': 'Ten Streak',
            'beschreibung_de': 'Beantworte 10 Fragen hintereinander richtig',
            'beschreibung_en': 'Answer 10 questions correctly in a row',
            'icon': '🔥🔥',
            'category': 'streak',
            'requirement_type': 'streak',
            'requirement_value': 10,
            'points': 50,
            'rarity': 'rare'
        },
        {
            'schluessel': 'PERFECT_GAME',
            'titel_de': 'Perfektes Spiel',
            'titel_en': 'Perfect Game',
            'beschreibung_de': 'Beende ein Spiel mit 100% richtigen Antworten',
            'beschreibung_en': 'Complete a game with 100% correct answers',
            'icon': '💎',
            'category': 'score',
            'requirement_type': 'percentage',
            'requirement_value': 100,
            'points': 100,
            'rarity': 'epic'
        },
        {
            'schluessel': 'GAMES_10',
            'titel_de': 'Veteran',
            'titel_en': 'Veteran',
            'beschreibung_de': 'Spiele 10 Spiele',
            'beschreibung_en': 'Play 10 games',
            'icon': '🎮',
            'category': 'games',
            'requirement_type': 'count',
            'requirement_value': 10,
            'points': 30,
            'rarity': 'common'
        },
        {
            'schluessel': 'SURVIVAL_MASTER',
            'titel_de': 'Survival-Meister',
            'titel_en': 'Survival Master',
            'beschreibung_de': 'Gewinne ein Survival-Hardcore-Spiel',
            'beschreibung_en': 'Win a Survival Hardcore game',
            'icon': '💀',
            'category': 'games',
            'requirement_type': 'count',
            'requirement_value': 1,
            'points': 150,
            'rarity': 'legendary'
        },
    ]
    
    for ach_data in achievements:
        ach = Achievement(**ach_data)
        db.session.add(ach)
    
    logger.info(f"Created {len(achievements)} achievements")

def initialize_avatar_parts():
    """Initialize avatar customization parts"""
    avatar_parts = [
        # Köpfe
        {'typ': 'Kopf', 'bezeichnung': 'Cyber-Helm', 'css_klasse': 'avatar-head-cyber', 'preis': 0},
        {'typ': 'Kopf', 'bezeichnung': 'Neon-Mohawk', 'css_klasse': 'avatar-head-mohawk', 'preis': 100},
        {'typ': 'Kopf', 'bezeichnung': 'Hologramm', 'css_klasse': 'avatar-head-holo', 'preis': 200},
        
        # Brillen
        {'typ': 'Brille', 'bezeichnung': 'Keine', 'css_klasse': 'avatar-glasses-none', 'preis': 0},
        {'typ': 'Brille', 'bezeichnung': 'Neon-Visor', 'css_klasse': 'avatar-glasses-visor', 'preis': 50},
        {'typ': 'Brille', 'bezeichnung': 'AR-Brille', 'css_klasse': 'avatar-glasses-ar', 'preis': 150},
        
        # Farben
        {'typ': 'Farbe', 'bezeichnung': 'Cyan', 'css_klasse': 'avatar-color-cyan', 'preis': 0},
        {'typ': 'Farbe', 'bezeichnung': 'Magenta', 'css_klasse': 'avatar-color-magenta', 'preis': 0},
        {'typ': 'Farbe', 'bezeichnung': 'Neon-Grün', 'css_klasse': 'avatar-color-neon-green', 'preis': 50},
        {'typ': 'Farbe', 'bezeichnung': 'Gold', 'css_klasse': 'avatar-color-gold', 'preis': 100},
    ]
    
    for part_data in avatar_parts:
        part = AvatarPart(**part_data)
        db.session.add(part)
    
    logger.info(f"Created {len(avatar_parts)} avatar parts")
