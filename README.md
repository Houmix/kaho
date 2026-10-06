# 🚗 Kaho - Plateforme d'Auto-École Moderne

> Plateforme web complète et offline-first pour une monitrice d'auto-école indépendante

## 🎯 Vue d'ensemble

Kaho est une plateforme SaaS conçue pour les monitrices d'auto-école indépendantes, offrant:

- **Mode offline-first**: Utilisation même sans connexion internet
- **Progressive Web App (PWA)**: Installation directe sur téléphones/tablettes
- **Gestion complète des élèves**: Réservations, suivi pédagogique, documents administratifs
- **Notifications automatiques**: Rappels SMS/Email 24h avant les leçons
- **Intégration Google Calendar**: Synchronisation du planning
- **Paiements Stripe**: Gestion des achats de paquets d'heures
- **Google Cloud Storage**: Stockage sécurisé des documents

## 🏗️ Architecture

### Backend (Django + DRF)
```
backend/
├── config/          # Configuration Django + Celery
├── core/            # App principale avec modèles
├── api/             # Routes DRF REST
├── tasks.py         # Tâches Celery (notifications)
└── requirements.txt
```

**Stack:**
- Django 4.2
- Django REST Framework 3.14
- PostgreSQL (base de données)
- Redis (cache + broker Celery)
- Celery (tâches asynchrones)
- SendGrid (emails)
- Twilio (SMS)
- Google Cloud Storage (fichiers)
- Stripe (paiements)

**Déploiement:** Railway.app

### Frontend (Next.js + React)
```
frontend/
├── public/          # PWA manifest + Service Worker
├── src/
│   ├── pages/       # Routes Next.js
│   ├── components/  # Composants réutilisables
│   ├── hooks/       # Hooks (auth, etc.)
│   ├── lib/         # Utilitaires (API, DB offline)
│   └── styles/      # Tailwind CSS
└── package.json
```

**Stack:**
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Axios (HTTP client)
- IndexedDB (cache offline)
- Zustand (state management)

**Déploiement:** Vercel

## 🗂️ Modèles de Données

### Core Models
1. **User** - Utilisateur (hérite de AbstractUser)
   - Rôles: INSTRUCTOR | STUDENT

2. **StudentProfile** - Profil élève
   - NEPH, heures achetées/utilisées, prêt pour examen

3. **MeetingPoint** - Points de rendez-vous
   - Nom, adresse, coordonnées GPS

4. **Slot** - Créneaux de leçon
   - Date/heure, statut, monitrice assignée, élève (si réservé)

5. **Lesson** - Bilan pédagogique
   - Présence, compétences REMC (JSON), conditions météo, notes
   - Lié à Slot en OneToOne

6. **Package** - Achat de paquets d'heures
   - Heures achetées, montant, statut Stripe

7. **Document** - Documents administratifs
   - Pièce d'identité, NEPH, contrats (stockés GCS)

8. **VehicleLog** - Suivi flotte
   - Kilométrage journalier, coût carburant, alertes maintenance

## 🔄 Workflows Principaux

### 1️⃣ Réservation d'une leçon (Élève)
```
Élève voit créneaux disponibles → Réserve → Monitrice notifiée → Rappel 24h avant
```

### 2️⃣ Validation d'une leçon (Monitrice - Hors-ligne)
```
Fin de cours → Formulaire validation (offline) → Synchronisation au retour réseau
→ Bilan enregistré → Heures déduites du crédit
```

### 3️⃣ Achat d'heures (Élève)
```
Élève achète pack → Paiement Stripe → Webhook confirmation → 
Package validé → Heures ajoutées au crédit
```

## 🚀 Installation & Développement

### Prérequis
- Python 3.11+
- Node.js 18+
- PostgreSQL 15
- Redis 7
- Git

### Backend Setup

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate  # or 'venv\Scripts\activate' on Windows

pip install -r requirements.txt
cp .env.example .env

# Configure .env with your database/Redis/API keys

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**En parallèle, démarrer Celery:**
```bash
celery -A config worker --loglevel=info
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local

# Configure NEXT_PUBLIC_API_URL

npm run dev
```

Frontend sera accessible sur `http://localhost:3000`

## 🔑 Clés de Configuration Requises

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost/kaho_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
SENDGRID_API_KEY=your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+33123456789
STRIPE_SECRET_KEY=your-stripe-key
GCS_BUCKET_NAME=kaho-documents
GCS_CREDENTIALS=path-to-service-account-json
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 📋 Endpoints API Principaux

### Authentification
- `POST /auth/token/` - Obtenir JWT access + refresh
- `POST /auth/token/refresh/` - Rafraîchir token

### Profils
- `GET /student-profiles/` - Lister les profils élèves
- `GET /student-profiles/my_profile/` - Mon profil
- `POST /student-profiles/` - Créer profil

### Créneaux
- `GET /slots/available_slots/` - Créneaux disponibles
- `POST /slots/{id}/book_slot/` - Réserver un créneau
- `POST /slots/{id}/cancel_slot/` - Annuler une réservation

### Leçons
- `GET /lessons/` - Lister mes leçons
- `POST /lessons/` - Créer un bilan pédagogique

### Documents
- `GET /documents/` - Mes documents
- `POST /documents/` - Upload document

### Paquets d'heures
- `GET /packages/` - Mes achats
- `POST /packages/` - Créer achat (paiement Stripe)

## 🛠️ Prochaines Étapes Importantes

### Phase 2 - Magic Links Authentication
- [ ] Implémenter endpoints de Magic Links (login sans mot de passe)
- [ ] Envoyer liens d'authentification via SendGrid
- [ ] Valider tokens OTP

### Phase 3 - Composants Avancés Frontend
- [ ] Calendrier de réservation (react-calendar)
- [ ] Formulaire de validation de leçon (composant hors-ligne)
- [ ] Upload de documents vers GCS
- [ ] Intégration Google Calendar (OAuth2)

### Phase 4 - Paiements Stripe
- [ ] Implémentation Stripe Elements
- [ ] Webhooks de paiement
- [ ] Factures automatiques

### Phase 5 - Testing
- [ ] Tests unitaires backend (Django TestCase)
- [ ] Tests intégration (Pytest + Fixtures)
- [ ] Tests frontend (Jest + React Testing Library)
- [ ] Tests PWA (Lighthouse audit)

### Phase 6 - Déploiement
- [ ] Configurer Railway pour le backend
- [ ] Déployer PostgreSQL managée
- [ ] Configurer Redis sur Railway
- [ ] Déployer frontend sur Vercel
- [ ] Configurer domaine personnalisé

## 📱 Features Offline (PWA)

**Service Worker cache strategy:**
- Assets statiques: Cache-first
- Requêtes API: Network-first, fallback cache
- Mutations offline: Queued en IndexedDB, synced au retour

**Données synchronisées au retour réseau:**
- Création/modification de leçons
- Annulation de réservations
- Uploads de documents

## 📞 Support & Documentation

- [Plan d'implémentation détaillé](PLAN.md)
- [Architecture technique](ARCHITECTURE.md)
- Issues/Bugs: Créer une issue GitHub

## 📄 Licence

Propriétaire - Tous droits réservés

---

**Made with ❤️ for independent driving instructors**
