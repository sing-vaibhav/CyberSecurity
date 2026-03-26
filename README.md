# CyberShield — Django Backend

A full Django-powered cybersecurity awareness website with REST API,
SQLite database, admin dashboard, and Django Admin panel.

---

## Project Structure

```
cybershield/
├── manage.py
├── requirements.txt
├── cybershield/              ← Django project package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── awareness/                ← Main Django app
    ├── models.py             ← 4 models: Subscriber, QuizResult, ThreatReport, PageVisit
    ├── views.py              ← All API views + page views
    ├── urls.py               ← URL routing
    ├── admin.py              ← Django Admin registrations
    ├── middleware.py         ← Request logging middleware
    └── templates/awareness/
        ├── index.html        ← Frontend (connected to API)
        └── admin.html        ← Stats dashboard
```

---

## Quick Start

### 1. Install Django
```bash
pip install django
```

### 2. Apply migrations
```bash
python manage.py makemigrations awareness
python manage.py migrate
```

### 3. Create a superuser (for Django Admin)
```bash
python manage.py createsuperuser
```

### 4. Run the development server
```bash
python manage.py runserver
```

### 5. Open in your browser
| URL | Description |
|-----|-------------|
| http://localhost:8000/ | Main awareness website |
| http://localhost:8000/dashboard/ | Live stats dashboard |
| http://localhost:8000/admin/ | Django Admin panel |

---

## REST API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/subscribe/` | Save email subscriber |
| POST | `/api/quiz/` | Submit quiz result |
| POST | `/api/report/` | Submit a threat report |
| POST | `/api/track/` | Track section engagement |
| GET  | `/api/stats/` | Get all dashboard stats |

### Example — Subscribe
```bash
curl -X POST http://localhost:8000/api/subscribe/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Example — Submit quiz result
```bash
curl -X POST http://localhost:8000/api/quiz/ \
  -H "Content-Type: application/json" \
  -d '{"score": 4, "total": 5, "answers": [{"q_idx":0,"chosen":1,"correct":true}]}'
```

### Example — Report a threat
```bash
curl -X POST http://localhost:8000/api/report/ \
  -H "Content-Type: application/json" \
  -d '{"type": "phishing", "description": "Fake PayPal email", "url": "http://paypa1.com"}'
```

---

## Database Models

### Subscriber
- `email` — unique email address
- `ip_hash` — anonymised SHA-256 of IP (first 16 chars)
- `is_active` — boolean, default True
- `created_at` — timestamp

### QuizResult
- `score` / `total` / `pct` — score tracking
- `answers` — JSON array of per-question answer details
- `ip_hash`, `created_at`

### ThreatReport
- `threat_type` — phishing / scam / malware / impersonation / public_wifi / ransomware / other
- `description` — free text (max 1000 chars)
- `suspect_url` — optional URL
- `ip_hash`, `created_at`

### PageVisit
- `section` — which section was engaged (hero, threats, quiz, etc.)
- `user_agent`, `ip_hash`, `created_at`

---

## Security Features
- **CSRF protection** on all POST endpoints (Django built-in)
- **Rate limiting** via in-memory cache (configurable per endpoint)
- **IP anonymisation** — IPs are hashed, never stored raw
- **Input validation** on all endpoints
- **Request logging** via custom middleware

---

## Switching to PostgreSQL

In `cybershield/settings.py`, replace the DATABASES block:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'cybershield'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

Then: `pip install psycopg2-binary`

---

## Production Checklist
- [ ] Set `DJANGO_SECRET_KEY` environment variable
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Run `python manage.py collectstatic`
- [ ] Use gunicorn + nginx in production
- [ ] Switch to PostgreSQL
- [ ] Add login protection to `/dashboard/`
