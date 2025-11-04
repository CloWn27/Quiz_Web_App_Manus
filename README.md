# 🌃 FiSi-Quiz-Cyberpunk

Eine interaktive Lernplattform im Cyberpunk-Design für Fachinformatiker Systemintegration (FiSi) Auszubildende.

## ✨ Features

### 🎮 Multiplayer-Modi
- **Klassisch**: Traditionelles Quiz-Format mit Punktesystem
- **Survival Normal**: Falsche Antworten führen zu Punktabzug
- **Survival Hardcore**: Eine falsche Antwort = Ausscheiden
- **Solo-Training**: Ungewertetes Training ohne Zeitdruck

### 🎯 Gameplay
- Echtzeit-Multiplayer via SocketIO
- Zeitbasierte Punkteberechnung (schneller = mehr Punkte)
- Multiple-Choice und Textfragen mit Fuzzy-Matching
- Schwierigkeitsgrade: Leicht, Mittel, Schwer, Heavy
- 5 Lernfelder mit Fachfragen

### 🏆 Progression & Customization
- Achievement-System mit automatischem Unlock
- Avatar-Customizer (Köpfe, Brillen, Farben)
- FiSi-Punkte & Bestenliste
- Streak-Tracking (aktuelle & beste Serie)
- Detaillierte Statistiken

### 🌍 Internationalisierung
- Vollständige DE/EN-Unterstützung
- Mehrsprachige Fragen und UI
- Sprachwechsel zur Laufzeit

### ⚙️ Admin-Features
- Fragen-Management (Hinzufügen, Bearbeiten, Löschen)
- Benutzer-Verwaltung
- Spiel-Übersicht
- Statistiken

## 🚀 Installation

### Voraussetzungen
- Python 3.11+
- pip3

### Lokale Installation

```bash
# Repository klonen
git clone https://github.com/CloWn27/Quiz_Web_App_Manus.git
cd Quiz_Web_App_Manus

# Dependencies installieren
pip3 install -r requirements.txt

# App starten
python3 app.py
```

Die App läuft dann auf `http://localhost:5000`

## 🗄️ Datenbank

Die App verwendet standardmäßig SQLite für einfaches Setup. In Produktion kann PostgreSQL verwendet werden.

### Initialisierung

Beim ersten Start werden automatisch erstellt:
- 5 Lernfelder
- 5 Beispielfragen für Lernfeld 5
- 6 Achievements
- 10 Avatar-Parts

## 🎨 Technologie-Stack

- **Backend**: Flask 3.0, Flask-SocketIO
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Frontend**: Tailwind CSS, Socket.IO Client
- **Real-time**: SocketIO für Multiplayer
- **Security**: Werkzeug Password Hashing, Flask-Talisman

## 📁 Projektstruktur

```
fisi-quiz-cyberpunk/
├── app.py                  # Haupt-Flask-App
├── models.py               # Datenbankmodelle
├── config.py               # Konfiguration
├── extensions.py           # Flask-Extensions
├── socketio_events.py      # SocketIO Event-Handler
├── requirements.txt        # Python-Dependencies
├── views/                  # Route-Blueprints
│   ├── main_routes.py
│   ├── auth_routes.py
│   ├── game_routes.py
│   ├── admin_routes.py
│   └── profile_routes.py
├── templates/              # Jinja2-Templates
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   ├── auth/
│   ├── game/
│   ├── admin/
│   └── profile/
├── static/                 # Statische Assets
│   ├── css/
│   ├── js/
│   └── images/
└── utils/                  # Hilfsfunktionen
    └── init_data.py
```

## 🎮 Spielablauf

1. **Registrierung/Login** oder Gast-Login
2. **Spiel erstellen** oder **beitreten** mit Raum-Code
3. **Lobby**: Warten auf weitere Spieler
4. **Spielstart**: Host startet das Spiel
5. **Fragen beantworten**: Gegen die Zeit und andere Spieler
6. **Ergebnisse**: Bestenliste und Achievement-Unlocks
7. **Statistiken**: Detaillierte Auswertung

## 🔧 Konfiguration

Umgebungsvariablen in `.env`:

```bash
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///fisi_quiz.db
CORS_ORIGINS=*
```

## 🌐 Deployment

### Render (Empfohlen)

1. Repository auf GitHub pushen
2. Render.com Account erstellen
3. "New Web Service" erstellen
4. Repository verbinden
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 app:app`

### Umgebungsvariablen auf Render

```
FLASK_HOST=0.0.0.0
FLASK_PORT=10000
FLASK_DEBUG=False
SECRET_KEY=<generate-random-key>
DATABASE_URL=<postgres-url>
```

## 📝 Lizenz

MIT License

## 👨‍💻 Entwickler

Entwickelt mit ❤️ für FiSi-Auszubildende

## 🤝 Beitragen

Pull Requests sind willkommen! Für größere Änderungen bitte zuerst ein Issue öffnen.

## 📧 Support

Bei Fragen oder Problemen bitte ein GitHub Issue erstellen.

---

**Made with Manus AI** 🤖
