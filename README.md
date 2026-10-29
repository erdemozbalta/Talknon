# Talknon

<p align="center">
  <a href="./README_TR.md"><img src="https://img.shields.io/badge/Language-Türkçe-E31E24?style=for-the-badge" alt="Türkçe" /></a>
  <a href="./README.md"><img src="https://img.shields.io/badge/Language-English-00247D?style=for-the-badge" alt="English" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/Socket.io-010101?style=for-the-badge&logo=socketdotio&logoColor=white" alt="Socket.io" />
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL" />
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript" />
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
</p>

Talknon is a location-based, real-time social networking platform that enables cafe visitors physically seated in the same venue to interact anonymously via table QR codes and GPS geofence verification, discover matching profiles, and initiate secure direct messaging (DM).

---

## Table of Contents

- [About the Project](#about-the-project)
- [Problem and Motivation](#problem-and-motivation)
- [Target Audience](#target-audience)
- [Features](#features)
- [Application Flow](#application-flow)
- [Screenshots](#screenshots)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Database Structure](#database-structure)
- [WebSocket and API Structure](#websocket-and-api-structure)
- [Installation and Setup](#installation-and-setup)
- [Project Structure](#project-structure)
- [Security and Moderation](#security-and-moderation)

---

## About the Project

Talknon is a full-stack web application bridging physical cafe experiences with real-time digital socialization. The system coordinates three distinct user roles within a unified ecosystem:

- **Customer (User):** Scans table QR codes, verifies physical presence via GPS geofencing, joins the cafe room under a custom anonymous nickname, participates in the public room chat, browses attendee cards, and initiates 1-on-1 private messaging (DM) upon mutual match approval.
- **Cafe Business:** Authenticates via a dedicated code (`TLK-XXXXXX`) to access the business management console, monitors live room conversations, mutes abusive chatters, enforces temporary or permanent cafe bans, and handles customer report logs.
- **Platform Administrator:** Defines new cafes across the system, manages geographic coordinates and coverage radiuses, auto-generates printable vector table QR codes, reviews global user profiles, and enforces network-wide disciplinary policies.

The server architecture is developed with Python/Flask, leveraging Flask-SocketIO and Eventlet for high-concurrency duplex WebSocket messaging. The persistence layer utilizes MySQL with SQLAlchemy ORM. The presentation tier is engineered with pure HTML5, CSS3 (Mobile-First responsive dark theme), and Vanilla JavaScript for frictionless, sub-second execution without framework bloat.

---

## Problem and Motivation

In modern public environments such as cafes, lounges, and coffeehouses, individuals frequently wish to connect and initiate conversations with people around them. However, fear of awkwardness, privacy hesitations, and lack of icebreakers prevent meaningful spontaneous interactions.

Conventional dating and messaging applications:
- Lack any verified physical connection to the specific venue.
- Match users located tens or hundreds of kilometers away.
- Fail to provide immediate on-site business moderation to ensure venue etiquette and customer safety.

**Talknon was designed to solve this:**

- **Table QR Code & GPS Geofencing:** Only patrons physically located within the cafe radius (e.g., 25–100 meters) can enter the room; spoofed locations are rejected.
- **True Anonymity & Privacy:** Users choose venue-specific nicknames without exposing phone numbers or real identities.
- **Mutual Match Approval:** Private direct messaging (DM) activates only when both parties accept the match request, preventing unsolicited intrusions.
- **Local Business Moderation:** Cafe managers have direct real-time tools to silence spam, ban rule violators, and maintain customer comfort.

---

## Target Audience

| Segment | Challenge | Solution |
|---------|-----------|----------|
| **Cafe Visitors** | Shyness and privacy concerns when meeting individuals in the same venue | Enter anonymous venue room via QR and GPS to chat and match safely |
| **Cafe Owners** | Need to boost on-premise customer engagement and brand loyalty | Dedicated dashboard, live chat oversight, visitor activity analytics |
| **Platform Administrator** | Centralized oversight across multi-branch cafe networks and security | Dynamic geofence setup, instant QR generator, global moderation suite |

---

## Features

### Customer (User) Module

- **QR-Based Room Access:** Instant routing to the cafe lobby simply by scanning physical table QR stickers.
- **GPS Geofence Validation:** Real-time distance measurement using the Haversine formula against verified cafe coordinates.
- **Dynamic Nickname System:** Selects a venue-specific persona upon entrance; real telephone numbers remain strictly hidden.
- **Real-Time Group Chat:** Zero-latency WebSocket group discussion with live participant count and distinct username coloring.
- **Dual-Opt-In Matching:** Send and receive match proposals with other users in the room.
- **Direct Messaging (DM):** Real-time, peer-to-peer encrypted chat thread opened exclusively upon reciprocal match acceptance.
- **Instant Unmatch:** Dynamic removal of conversation threads and user cards across both devices without page reloads.
- **Block & Report Engine:** Ability to block disruptive peers and submit flagged messages with categorized reasons to managers.
- **Profile & Preferences:** Avatar upload, password update, blocked user management, and locale switching (Turkish / English).

### Cafe Business Module

- **Dedicated Business Portal:** Secure login utilizing unique cafe codes (`TLK-XXXXXX`) and business credentials.
- **Live Room Monitor:** Real-time stream of cafe conversations and connected patron statistics.
- **Venue-Level Banning:** Revoke venue access for specific users temporarily or permanently.
- **Chat Muting:** Apply temporary cooldown timers to suppress spamming users.
- **Report Review Console:** Evaluate reported messages and take instant disciplinary action.
- **Cafe Analytics:** Monitor daily sessions, active chat counts, total messages, and match numbers.

### Administrator (Admin) Module

- **Cafe Management:** Create cafe profiles, set map coordinates, configure geofencing radiuses.
- **Automated QR Generation:** Automatic production of high-definition, printable table QR graphics upon venue creation.
- **Global User Oversight:** Audit all registered profiles, inspect roles, and execute platform-wide bans or account deletions.
- **Central Security Hub:** Unified console to review reported logs, active restrictions, and security alerts.
- **System Metrics:** Real-time aggregated statistics covering total users, cafes, daily messages, and active socket sessions.

---

## Application Flow

End-to-end operational lifecycle:

```
Stage 1 — Platform Configuration (Admin)
1. Admin        → Logs into administrative console.
2. Admin        → Registers new cafe profile (Name, GPS coordinates, geofence radius).
3. Admin        → Platform auto-generates venue code and high-resolution table QR codes.
4. Admin        → Delivers access credentials and printable QR graphics to cafe owner.

Stage 2 — Venue Verification & Check-In (Customer)
1. Customer     → Scans table QR code with smartphone.
2. System       → Prompts browser for GPS location and calculates distance via Haversine.
3. Customer     → Upon location verification, customer enters lobby and sets temporary nickname.
4. Customer     → Joins cafe live room.

Stage 3 — Live Socialization & Matching (Customer)
1. Customer     → Exchanges real-time messages in the public cafe feed.
2. Customer     → Taps on a user card to dispatch a match request.
3. Recipient    → Receives an instant notification toast; accepting unlocks the 1-on-1 DM channel.
4. Both Parties → Conduct private conversations; either user can terminate the match at any moment.

Stage 4 — Moderation & Governance (Business & Admin)
1. Business     → Monitors live chat stream from the business terminal.
2. Customer     → Flags an abusive message.
3. Business     → Imposes a chat cooldown or kicks/bans the offending patron from the venue.
4. Admin        → Enforces platform-wide ban in cases of severe infractions.
```

---

## Screenshots

### Customer (User) Screens

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/user/login.png" width="220"/><br/><sub><b>User Login</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/qr_scan_entry.png" width="220"/><br/><sub><b>QR Scan Entry</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/live_chat.png" width="220"/><br/><sub><b>Live Cafe Chat</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/match_success.png" width="220"/><br/><sub><b>Match Notification</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/user/dm_chat.png" width="220"/><br/><sub><b>Direct Message (DM)</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/dm_match_requests.png" width="220"/><br/><sub><b>Match Proposals</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/unmatch.png" width="220"/><br/><sub><b>Unmatch Dialog</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/settings.png" width="220"/><br/><sub><b>Account Settings</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/user/profile.png" width="220"/><br/><sub><b>Profile Management</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/change_nickname.png" width="220"/><br/><sub><b>Nickname Update</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/report_message.png" width="220"/><br/><sub><b>Report Message</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/blocked_users.png" width="220"/><br/><sub><b>Blocked Users</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/user/spam_protection_toast.png" width="220"/><br/><sub><b>Spam Protection Toast</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/banned_nickname_notice.png" width="220"/><br/><sub><b>Banned Nickname Toast</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/system_banned_screen.png" width="220"/><br/><sub><b>Suspended Screen</b></sub></td>
    <td align="center"><img src="docs/screenshots/user/unblock_confirm.png" width="220"/><br/><sub><b>Unblock Dialog</b></sub></td>
  </tr>
</table>

### Cafe Business Screens

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/business/business_login.png" width="220"/><br/><sub><b>Business Portal Login</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/dashboard_1.png" width="220"/><br/><sub><b>Business Dashboard</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/cafe_chat.png" width="220"/><br/><sub><b>Live Chat Supervision</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/active_chat_users.png" width="220"/><br/><sub><b>Connected Users</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/business/reports.png" width="220"/><br/><sub><b>Flagged Content Queue</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/ban_from_cafe.png" width="220"/><br/><sub><b>Cafe Ban Modal</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/ban_message.png" width="220"/><br/><sub><b>Chat Mute Cooldown</b></sub></td>
    <td align="center"><img src="docs/screenshots/business/cafe_security.png" width="220"/><br/><sub><b>Security Center</b></sub></td>
  </tr>
</table>

### Administrator Screens

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/admin/stats.png" width="220"/><br/><sub><b>Platform Analytics</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/add_cafe_1.png" width="220"/><br/><sub><b>Add New Venue</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/cafe_created.jpg" width="220"/><br/><sub><b>Venue Created & QR</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/cafe_details.jpg" width="220"/><br/><sub><b>Cafe Overview</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/admin/users_list.png" width="220"/><br/><sub><b>User Directory</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/ban_user.png" width="220"/><br/><sub><b>Global User Ban</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/security_center.png" width="220"/><br/><sub><b>Platform Security Hub</b></sub></td>
    <td align="center"><img src="docs/screenshots/admin/edit_cafe_1.png" width="220"/><br/><sub><b>Edit Cafe Profile</b></sub></td>
  </tr>
</table>

---

## Tech Stack

| Layer | Technology | Description |
|-------|------------|-------------|
| **Backend** | Python 3.11+ / Flask | Modular Application Factory design |
| **Real-Time Engine** | Flask-SocketIO + Eventlet | Duplex WebSocket pipelines for chat and notifications |
| **Database** | MySQL 8.x | Relational storage engine with `utf8mb4` charset |
| **ORM** | Flask-SQLAlchemy | Schema modeling, relations, and automatic table creation |
| **Security & CSRF** | Flask-WTF + Flask-Limiter | CSRF token validation and rate limiting against spam/DoS |
| **Session & Auth** | Flask-Login + Werkzeug | PBKDF2 (SHA-256) password hashing and session tokens |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Lightweight, mobile-first responsive dark theme UI |
| **Geofencing Engine** | Geolocation API + Haversine | GPS coordinate checks against cafe meters radius |
| **QR Generation** | Python qrcode[pil] + Pillow | Automated high-res table QR image compilation |
| **Internationalization** | Built-in i18n Engine | Dynamic Turkish and English language switching |

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│               Client Tier (Mobile / Browser)               │
│                                                            │
│   Responsive UI  |  Vanilla JS  |  Socket.IO Client        │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           │  HTTP / WebSocket (WSS)
                           │
┌──────────────────────────▼─────────────────────────────────┐
│               Python / Flask Web Application               │
│                                                            │
│  Blueprints:                                               │
│  ├── /auth     (Register, Login, SMS, Business Login)      │
│  ├── /chat     (Cafe Lobby, Group Room)                    │
│  ├── /dm       (Match Proposals, Private DM)               │
│  ├── /user     (Profile, Settings, Block List)             │
│  ├── /business (Business Console, Room Moderation)         │
│  └── /admin    (Venue Setup, QR Generator, Security)       │
│                                                            │
│  Socket.IO Event Handlers:                                 │
│  ├── chat_events (send_message, join_room, report)         │
│  └── dm_events   (send_dm, match_request, unmatch)         │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           │  SQLAlchemy ORM
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                     MySQL Database                         │
│                                                            │
│  11 Tables  |  Relational Data Model  |  utf8mb4 Support   │
└────────────────────────────────────────────────────────────┘
```

---

## Database Structure

Primary models defined via SQLAlchemy:

| Table | Description |
|-------|-------------|
| `users` | All platform accounts (Patrons, Business, Admin) including credentials and roles. |
| `cafes` | Venue directory including slugs, unique codes (`TLK-XXX`), GPS points, and QR paths. |
| `cafe_sessions` | Temporary user entrance records and active venue nicknames. |
| `messages` | Public messages broadcast within cafe rooms. |
| `direct_messages` | Private 1-on-1 messages exchanged between matched patrons. |
| `dm_clearances` | Audit records for users opting to purge their personal message histories. |
| `match_requests` | Proposals and state machine (`pending`, `accepted`, `rejected`, `unmatched`). |
| `reports` | Flagged message logs submitted by patrons for disciplinary review. |
| `bans` | Venue-specific or system-wide restriction and suspension records. |
| `blocks` | Peer-to-peer user block relationships. |
| `cafe_stats` | Aggregate daily metrics tracking messages, sessions, and interactions. |

---

## WebSocket and API Structure

Flask-SocketIO event communication:

| Event Name | Direction | Description |
|------------|-----------|-------------|
| `join` | Client → Server | Connects patron socket to specific cafe room channel |
| `send_message` | Client → Server | Dispatches new message to public cafe feed |
| `new_message` | Server → Client | Broadcasts message payload to all active room listeners |
| `send_dm` | Client → Server | Dispatches private message to matched counterpart |
| `receive_dm` | Server → Client | Delivers DM message directly to recipient socket |
| `match_request` | Client → Server | Submits match proposal to target user |
| `match_request_received` | Server → Client | Alerts recipient socket with instant notification toast |
| `match_accepted` | Server → Client | Dynamically unlocks private DM thread on both clients |
| `match_removed` | Server → Client | Dynamically purges cards and redirects upon unmatch |

---

## Installation and Setup

### Prerequisites

- [Python 3.11 or higher](https://www.python.org/)
- [MySQL Server](https://dev.mysql.com/downloads/) or [XAMPP](https://www.apachefriends.org/)
- [Git](https://git-scm.com/)

### 1. Clone Repository

```bash
git clone https://github.com/jnost/Talknon.git
cd Talknon
```

### 2. Configure Virtual Environment and Dependencies

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Initialize MySQL Database

Create an empty database via MySQL shell or phpMyAdmin:

```sql
CREATE DATABASE talknon CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configure Environment Variables

Duplicate `.env.example` as `.env` and fill in credentials:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=super-secret-key-change-this

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=talknon

DEFAULT_ADMIN_PHONE=+905000000000
DEFAULT_ADMIN_PASSWORD=admin123
```

### 5. Launch Application

```powershell
python run.py
```

*The application automatically creates all database tables and the default administrator account on first boot.*  
Open your browser and navigate to `http://localhost:5000`.

---

## Project Structure

```
Talknon/
├── app/
│   ├── blueprints/           # Modular route controllers
│   │   ├── admin/            # Venue setup, user directory, security
│   │   ├── auth/             # Patron and business authentication
│   │   ├── business/         # Business dashboard and room moderation
│   │   ├── chat/             # Public lobby and group chat
│   │   ├── dm/               # Direct messaging and match workflow
│   │   └── user/             # Profile, settings, and blocked users
│   ├── models/               # SQLAlchemy models
│   ├── services/             # Domain services (Location, QR generator, Spam guard)
│   ├── socket_events/        # Real-time WebSocket event dispatchers
│   ├── static/               # CSS styles, Vanilla JS scripts, and assets
│   ├── templates/            # HTML Jinja templates
│   ├── utils/                # Helpers, security decorators, i18n
│   ├── config.py             # Development / Production configurations
│   ├── extensions.py         # SQLAlchemy, SocketIO, Limiter instances
│   └── __init__.py           # Application Factory and bootloader
├── docs/
│   └── screenshots/          # Showcase screenshots
│       ├── admin/
│       ├── business/
│       └── user/
├── run.py                    # Application launch script
├── requirements.txt          # Package dependencies
├── .env.example              # Sample environment configuration
├── .gitignore
└── README.md
```

---

## Security and Moderation

- **Cryptography:** Credentials protected using Werkzeug PBKDF2 (SHA-256) password hashing.
- **CSRF Defense:** All state-modifying requests secured via `Flask-WTF` CSRF tokens.
- **Rate Limiting:** `Flask-Limiter` regulates message and request velocity per IP/account.
- **Geofence Enforcement:** GPS coordinates verified via the Haversine formula to reject remote entry.
- **Role Guards:** Privileged actions locked behind `@admin_required` and `@business_required` decorators.
- **Dual-Sided Dynamic Purge:** Unmatching automatically cleans threads across both clients in real time.

---



<p align="center">
  Copyright &copy; 2026 Erdem Özbalta. All rights reserved.<br/>
  <a href="mailto:erdemozbalta@gmail.com">erdemozbalta@gmail.com</a>
</p>
