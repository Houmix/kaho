# 🚀 Guide de Démarrage Rapide - Kaho

## 📋 Pré-requis installés
- Python 3.11+
- Node.js 18+
- PostgreSQL 15
- Redis 7

## ⚡ Démarrage en 5 minutes

### 1️⃣ Cloner et configurer

```bash
cd /Users/lachachehoumame/Documents/kaho

# Créer le virtualenv backend
cd backend
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos infos locales (optionnel pour dev local)
```

### 2️⃣ Initialiser la base de données

```bash
# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un super-utilisateur (monitrice)
python manage.py createsuperuser
# Email: instructeur@kaho.app
# Password: your-password
# Role: INSTRUCTOR (laisser vide et taper manuellement si besoin)
```

### 3️⃣ Démarrer le backend

**Terminal 1 - Django server:**
```bash
python manage.py runserver
# Accessible sur http://localhost:8000
# Admin sur http://localhost:8000/admin
```

**Terminal 2 - Celery worker:**
```bash
celery -A config worker --loglevel=info
```

**Terminal 3 - Celery beat (optionnel pour dev):**
```bash
celery -A config beat --loglevel=info
```

### 4️⃣ Démarrer le frontend

```bash
cd ../frontend
npm install  # Si pas encore fait
npm run dev
# Accessible sur http://localhost:3000
```

## 🎯 Test rapide

### Créer des données de test

```bash
# Dans Django shell
python manage.py shell
```

```python
from core.models import User, StudentProfile, MeetingPoint, Slot
from django.utils import timezone
from datetime import datetime, timedelta

# 1. Créer un élève
student = User.objects.create_user(
    username='eleve@test.com',
    email='eleve@test.com',
    first_name='Jean',
    last_name='Dupont',
    password='testpass123',
    role='STUDENT'
)

# 2. Son profil
profile = StudentProfile.objects.get(user=student)
profile.purchased_hours = 20
profile.save()

# 3. Créer un point de RDV
meeting_point = MeetingPoint.objects.create(
    name='Gare Centrale',
    address='123 Rue de la Gare, Paris 75000',
    latitude='48.8456',
    longitude='2.3522'
)

# 4. Créer des créneaux disponibles
instructor = User.objects.filter(role='INSTRUCTOR').first()
for i in range(5):
    date = timezone.now().date() + timedelta(days=i)
    Slot.objects.create(
        date=date,
        start_time='09:00',
        end_time='10:00',
        meeting_point=meeting_point,
        instructor=instructor,
        status='AVAILABLE'
    )

print("✅ Données de test créées!")
exit()
```

### Tester l'API

```bash
# Login
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "eleve@test.com",
    "password": "testpass123"
  }'

# Copier le token access et remplacer TOKEN ci-dessous

# Récupérer les créneaux disponibles
curl http://localhost:8000/api/slots/available_slots/ \
  -H "Authorization: Bearer TOKEN"

# Obtenir mon profil
curl http://localhost:8000/api/student-profiles/my_profile/ \
  -H "Authorization: Bearer TOKEN"
```

### Tester le frontend

1. Ouvrir http://localhost:3000
2. Cliquer sur "Se connecter"
3. Entrer: `eleve@test.com` / `testpass123`
4. Voir le dashboard élève

## 🔧 Configuration Variables d'Environnement

### Backend `.env` (minimum pour dev)

```env
SECRET_KEY=dev-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database locale
DB_NAME=kaho_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis local
REDIS_URL=redis://localhost:6379/0

# Email/SMS (optionnels en dev, les tâches Celery fonctionneront sans)
SENDGRID_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Stripe (optionnel en dev)
STRIPE_SECRET_KEY=

# GCS (optionnel en dev, fichiers iront en local media/)
USE_GCS=False
```

### Frontend `.env.local` (minimum)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 📊 Admin Django

Accédez à http://localhost:8000/admin avec les creds du super-user pour:
- Gérer les utilisateurs et leurs rôles
- Créer/éditer des créneaux
- Consulter les leçons validées
- Voir les documents uploads
- Parcourir les transactions

## 🐛 Troubleshooting

### "Module not found: next-pwa"
```bash
cd frontend
npm install next-pwa
```

### "postgresql: command not found"
```bash
# Sur Mac
brew install postgresql

# Démarrer PostgreSQL
brew services start postgresql
```

### "redis-server: command not found"
```bash
# Sur Mac
brew install redis

# Démarrer Redis
brew services start redis
```

### Migrations crash
```bash
# Reset complet de la DB (DEV ONLY!)
python manage.py flush
python manage.py migrate

# ou supprimer et recréer la DB
dropdb kaho_db
createdb kaho_db
python manage.py migrate
```

## ✅ Checklist Post-Démarrage

- [ ] Django server tourne sur 8000
- [ ] Celery worker actif (visible dans terminal)
- [ ] Frontend accessible sur 3000
- [ ] Données de test créées
- [ ] Peut se connecter avec compte élève
- [ ] Peut réserver un créneau
- [ ] Service Worker enregistré (DevTools > Application > Service Workers)

## 📚 Prochaines Étapes

1. **Implémenter Magic Links** (authentification par email)
2. **Ajouter composants avancés** (calendrier réservation, validation leçon)
3. **Intégrer paiements Stripe**
4. **Configurer notifications réelles** (SendGrid + Twilio)
5. **Tests unitaires + intégration**
6. **Déployer sur Railway + Vercel**

---

**Besoin d'aide?** Vérifiez la structure dans `STRUCTURE.md` ou consultez `README.md`
