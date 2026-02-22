# CLAUDE.md - Contexte projet ISIC Odoo

## Projet

Systeme de gestion academique pour l'ISIC (Institut Superieur de l'Information et de la Communication, Rabat) base sur **Odoo 19**. Projet proprietaire ISIC.

Repo: `isic-v1/` — image Docker officielle `odoo:19.0` + modules personnalises dans `custom-addons/`.

## Stack technique

- **Framework**: Odoo 19 (Python 3.10+, PostgreSQL 16)
- **Image Docker**: `odoo:19.0` (image officielle, pas de build source)
- **DB dev**: `isic_dev` — user `odoo`, password `odoo`, port `5434` (expose via Docker)
- **Serveur dev**: `http://localhost:8069`
- **Linting**: Ruff (line-length 120, cible py310)
- **Tests**: Odoo test runner via `make test MODULE=nom`
- **Docker**: docker-compose multi-env (dev local, VPS-4 prod+staging)
- **Pre-commit**: hooks ruff, bandit, pylint-odoo, pre-commit-hooks
- **CI Config**: `pyproject.toml` pour ruff, bandit, pytest, coverage
- **CI/CD**: GitHub Actions (lint, build GHCR, deploy avec rollback)
- **VPS-4**: OVH (48 GB RAM, 12 vCPU) — IP `51.178.47.204` — Odoo prod+staging
- **VPS-3**: OVH (22 GB RAM, 8 vCPU) — IP `51.255.200.172` — Auth (CAS+LDAP)

## Commandes essentielles

```bash
make run                    # Demarrer Odoo + PostgreSQL (docker compose up -d)
make stop                   # Arreter les conteneurs
make restart                # Redemarrer
make logs                   # Voir les logs
make shell                  # Bash dans le conteneur Odoo
make odoo-shell             # Console Odoo interactive
make update MODULE=nom      # Mettre a jour un module (-u + restart)
make scaffold NAME=nom      # Creer un nouveau module dans custom-addons/
make test MODULE=nom        # Tester un module
make lint                   # Ruff check custom-addons
make format                 # Ruff format + fix
make build                  # Construire l'image Docker
make build-no-cache         # Build sans cache
make pgadmin                # Demarrer pgAdmin (port 5050)
make db-backup              # Dump SQL dans backups/
make db-restore             # Restaurer la derniere sauvegarde
make pre-commit             # Installer les hooks pre-commit
make clean                  # Nettoyer __pycache__, .pyc
```

## Architecture du projet

```
isic-v1/
├── custom-addons/              # Modules Odoo personnalises (monte en volume dev)
│   ├── isic_theme/             # Branding ISIC + look enterprise-like
│   └── third-party/            # Modules tiers (MuK Web Theme + deps)
│       ├── muk_web_theme/      # Theme CE (v19.0.1.4.2, LGPL-3)
│       ├── muk_web_appsbar/
│       ├── muk_web_chatter/
│       ├── muk_web_colors/
│       ├── muk_web_dialog/
│       ├── muk_web_group/
│       └── muk_web_refresh/
├── docker/
│   ├── Dockerfile              # Image basee sur odoo:19.0
│   ├── entrypoint.sh           # Generation odoo.conf depuis env vars
│   ├── docker-compose.vps4.yml # VPS-4 Prod + Staging unifie (7 services actifs)
│   ├── docker-compose.auth-vps.yml  # VPS-3 Auth Stack (LDAP+CAS+phpLDAPadmin+Nginx)
│   ├── .env.vps3.template      # Variables VPS-3 (LDAP/CAS passwords)
│   ├── init-ldap-vps.sh        # Script init LDAP (overlays memberOf + donnees)
│   ├── logrotate/odoo.conf     # Rotation logs Odoo (daily, 14 jours)
│   ├── cas/                    # Image CAS custom (Apereo 6.6.15 + LDAP + branding ISIC)
│   │   ├── Dockerfile          # Multi-stage: Gradle (LDAP JARs) + CAS WAR overlay
│   │   ├── config/cas.properties   # Config CAS → LDAP auth, service registry, tickets
│   │   ├── services/OdooISIC-1001.json  # Service CAS (*.isic.ac.ma)
│   │   ├── overlay-build/      # Gradle build pour telecharger les JARs LDAP
│   │   └── overlay/static-override/  # Branding ISIC (CSS, JS, logo)
│   ├── ldap/
│   │   ├── bootstrap/01-isic-structure.ldif  # Structure annuaire ISIC (OUs, groupes, users)
│   │   └── config/memberof.ldif  # Config overlay memberOf
│   └── nginx/
│       ├── vps4.conf           # Reverse proxy VPS-4 (Odoo dual-domain)
│       ├── auth.conf           # Reverse proxy VPS-3 (CAS + phpLDAPadmin)
│       └── ssl/                # Certificats SSL (hors Git)
├── .github/workflows/
│   ├── ci.yml                  # Lint + XML/YAML validate + Docker build + Odoo tests
│   ├── build-push.yml          # Build & push vers GHCR (on push main/tags)
│   └── deploy.yml              # Deploy staging puis production (workflow_dispatch)
├── scripts/
│   ├── backup.sh               # pg_dump + gzip + retention
│   ├── generate_deployment_doc.py  # Generation doc DOCX deploiement VPS-4
│   └── generate_vps3_doc.py    # Generation doc DOCX deploiement VPS-3
├── docker-compose.yml          # Dev local (Odoo + PostgreSQL + pgAdmin)
├── .env.template               # Variables dev
├── .env.vps4.template          # Variables VPS-4
├── Makefile                    # Commandes projet
├── pyproject.toml              # Config ruff, bandit, pytest, coverage
├── .pre-commit-config.yaml     # Hooks pre-commit
├── requirements.txt            # Deps Python supplementaires (redis, python-ldap)
└── .gitignore                  # CLAUDE.md ignore (local uniquement)
```

## Structure de fichiers d'un module Odoo

```
module_name/
├── __manifest__.py     # Metadonnees
├── __init__.py
├── models/             # Modeles ORM
├── views/              # Vues XML
├── controllers/        # Controleurs HTTP
├── wizards/            # Assistants
├── reports/            # Rapports QWeb
├── data/               # Donnees initiales
├── security/           # ir.model.access.csv + ir.rule
├── static/             # JS, CSS, images
└── tests/              # Tests unitaires
```

## Docker — Developpement local

Image basee sur `odoo:19.0` officielle. L'entrypoint genere `/etc/odoo/odoo.conf` dynamiquement depuis les variables d'environnement.

- `custom-addons/` monte en volume `:ro` (edition live, pas besoin de rebuild)
- DB PostgreSQL 16 Alpine, port expose `5434` (evite conflit avec PostgreSQL local)
- pgAdmin disponible via `make pgadmin` (port 5050, profile `tools`)
- `DEV_MODE=all` active en dev (auto-reload assets + templates)

Chemins dans le conteneur :
- Addons: `/mnt/extra-addons` (custom) + `/usr/lib/python3/dist-packages/odoo/addons` (core)
- Data: `/var/lib/odoo`
- Config: `/etc/odoo/odoo.conf` (genere au demarrage)

## Docker — VPS-4 (Production + Staging)

Compose unifie `docker/docker-compose.vps4.yml`. Etat actuel : 7 services actifs, PgBouncer present mais pas branche (Odoo connecte directement aux DB).

```
VPS-4 (48 GB RAM, 12 vCPU) — 51.178.47.204
┌──────────────────────────────────────────────────┐
│ UFW Firewall (22, 80, 443 uniquement)            │
│ fail2ban (ban SSH brute force apres 3 echecs/1h) │
│                                                  │
│ Nginx (80/443) — certificats auto-signes         │
│  ├─ mon.isic.ac.ma → odoo-prod                  │
│  └─ staging.isic.ac.ma → odoo-staging           │
│                                                  │
│ odoo-prod → db-prod (connexion directe)          │
│ odoo-staging → db-staging (connexion directe)    │
│ Redis (sessions partagees, prefixes isoles)      │
│ Backup (cron 2h/jour, retention 7j)             │
└──────────────────────────────────────────────────┘
```

### Etat deploiement VPS (Fevrier 2026)

| Service | Container | Status |
|---------|-----------|--------|
| db-prod | isic-db-prod | healthy |
| db-staging | isic-db-staging | healthy |
| odoo-prod | isic-odoo-prod | healthy |
| odoo-staging | isic-odoo-staging | healthy |
| redis | isic-redis-vps | up |
| nginx | isic-nginx-vps4 | up (SSL auto-signe) |
| backup | isic-backup-vps | up (cron 2h) |

### PgBouncer (prevu, pas encore branche)

Services `pgbouncer-prod` et `pgbouncer-staging` definis dans le compose mais Odoo pointe directement vers `db-prod`/`db-staging`. PgBouncer sera active quand la charge le necessitera (>50 connexions concurrentes). Mode `session` requis (cron Odoo avec SAVEPOINT/SET). Image `edoburu/pgbouncer:latest`.

### Redis

Sessions partagees avec prefixes isoles : `odoo_prod_session` / `odoo_staging_session`.
Conditionnel dans `entrypoint.sh` (active si `REDIS_HOST` est defini).

### Nginx

- Reverse proxy dual-domain : `mon.isic.ac.ma` (prod) + `staging.isic.ac.ma`
- Certificats SSL auto-signes (Let's Encrypt a configurer quand DNS publics prets)
- TLS 1.2/1.3, OCSP stapling pret
- Rate limiting : login 5r/m (prod), API 10r/s
- WebSocket support (`/longpolling`, `/websocket`)
- Let's Encrypt ACME challenge pret (`/.well-known/acme-challenge/`)
- Cache static assets : 90j prod, 7j staging
- Headers securite : HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection

### Backup

Cron quotidien 2h via `scripts/backup.sh` : `pg_dump` compresse + rotation automatique.
Le service backup se connecte directement a `db-prod` (pas via PgBouncer).
Teste manuellement avec succes : `docker exec isic-backup-vps sh /backup.sh`

### Log rotation

- Docker : `json-file` driver avec `max-size`/`max-file` (Odoo 50m x5, autres 10m x3)
- Fallback logrotate : `docker/logrotate/odoo.conf` (daily, 14 jours, copytruncate)

### Ressources memoire

| Service | Limit | Reservation |
|---------|-------|-------------|
| odoo-prod | 4 GB | 1 GB |
| odoo-staging | 2 GB | 512 MB |
| db-prod | 2 GB | 512 MB |
| db-staging | 1 GB | 256 MB |
| redis | 256 MB | - |
| nginx | 256 MB | - |
| pgbouncer | 128 MB | - |

## Docker — VPS-3 (Auth Stack : CAS + LDAP)

Compose `docker/docker-compose.auth-vps.yml`. 4 services : OpenLDAP, phpLDAPadmin, Apereo CAS 6.6.15, Nginx.

```
VPS-3 (22 GB RAM, 8 vCPU) — 51.255.200.172
┌──────────────────────────────────────────────────┐
│ UFW Firewall (22, 80, 443 + 1389 pour VPS-4)    │
│ fail2ban (ban SSH brute force apres 3 echecs/1h) │
│                                                  │
│ Nginx (80/443) — certificats auto-signes         │
│  ├─ auth.isic.ac.ma → CAS (port 8443)           │
│  └─ ldap.isic.ac.ma → phpLDAPadmin (port 80)    │
│                                                  │
│ CAS 6.6.15 → OpenLDAP (bind + search)           │
│ OpenLDAP (dc=isic,dc=ac,dc=ma) — port 1389 expose     │
└──────────────────────────────────────────────────┘
     LDAP port 1389 ──→ VPS-4 (51.178.47.204 uniquement)
```

### Etat deploiement VPS-3 (Fevrier 2026)

| Service | Container | Status |
|---------|-----------|--------|
| OpenLDAP | isic-ldap-vps | healthy |
| phpLDAPadmin | isic-phpldapadmin-vps | up |
| CAS | isic-cas-vps | healthy |
| Nginx | isic-nginx-auth-vps | up (SSL auto-signe) |

### OpenLDAP

- Image : `osixia/openldap:1.5.0`
- Base DN : `dc=isic,dc=ac,dc=ma`
- Overlays : memberOf + refint (maintenance automatique des appartenances)
- Port hote : 1389 (UFW : VPS-4 only)
- TLS : desactive (communication interne Docker)
- Volumes persistants : `isic-ldap-data-vps` + `isic-ldap-config-vps`

### Structure annuaire LDAP

```
dc=isic,dc=ac,dc=ma
├── ou=People
│   ├── ou=Staff (5 users: directeur, admin.scolarite, agent.scolarite, resp.ci, prof.informatique)
│   └── ou=Students (3 users: etudiant1, etudiant2, etudiant3)
├── ou=Groups (4 groups: direction, enseignants, scolarite, etudiants)
└── ou=Services (1 bind account: odoo_bind)
```

### Apereo CAS

- Image : `isic-cas:latest` (build custom multi-stage : Gradle LDAP JARs + CAS WAR overlay)
- Version : 6.6.15
- JVM : -Xms512m -Xmx1536m
- Port interne : 8443 (HTTP, SSL termine par Nginx)
- URL : `https://auth.isic.ac.ma/cas`
- Auth : LDAP AUTHENTICATED (bind + search sur `ou=People,dc=isic,dc=ac,dc=ma`)
- Auth statique : desactivee (`cas.authn.accept.enabled=false`)
- Attributs releases : uid, cn, mail, sn, givenName, memberOf, employeeType
- Service registry : JSON (pattern `^https://.*\.isic\.ac\.ma/.*`)
- TGT : max 8h, kill 2h
- SLO : active (async)
- Branding : logo ISIC, CSS custom, labels FR

### Nginx VPS-3

- Reverse proxy dual-domain : `auth.isic.ac.ma` (CAS) + `ldap.isic.ac.ma` (phpLDAPadmin)
- Rate limiting CAS login : 10r/m
- HSTS + OCSP commentes (certificats auto-signes)
- IP restriction phpLDAPadmin : bloc commente, a activer avant production

### Communication inter-VPS

| Flux | Source | Destination | Port | Protocole |
|------|--------|-------------|------|-----------|
| Auth CAS | Navigateur → VPS-3 | Nginx → CAS | 443 | HTTPS (CAS 3.0) |
| Ticket CAS | Odoo (VPS-4) → VPS-3 | CAS | 443 | HTTPS (validation) |
| LDAP interne | CAS | OpenLDAP | 389 | LDAP |
| LDAP externe | VPS-4 (51.178.47.204) | OpenLDAP | 1389 | LDAP (UFW filtered) |

## Securite VPS

### Pare-feu (UFW)

Politique identique sur les 2 VPS : deny incoming, allow outgoing.

**VPS-4 (51.178.47.204)** :

| Port | Service | Source |
|------|---------|--------|
| 22 | SSH | Toutes |
| 80 | HTTP (redirect HTTPS) | Toutes |
| 443 | HTTPS (Nginx) | Toutes |

**VPS-3 (51.255.200.172)** :

| Port | Service | Source |
|------|---------|--------|
| 22 | SSH | Toutes |
| 80 | HTTP (redirect HTTPS) | Toutes |
| 443 | HTTPS (Nginx) | Toutes |
| 1389 | LDAP | 51.178.47.204 (VPS-4 uniquement) |

### fail2ban

Actif sur les 2 VPS :
- 3 echecs SSH en 10 minutes → ban 1 heure via UFW
- Config : `/etc/fail2ban/jail.local`
- Verifier : `sudo fail2ban-client status sshd`

### Isolation reseau Docker

**VPS-4** :
- `isic-internal-vps` (bridge, `internal: true`) : DB, Odoo, Redis, Backup — pas d'acces Internet
- `isic-external-vps` (bridge) : Nginx uniquement

**VPS-3** :
- `isic-auth-internal-vps` (bridge, `internal: true`) : LDAP, CAS, phpLDAPadmin — pas d'acces Internet
- `isic-auth-external-vps` (bridge) : Nginx uniquement

### Gestion des secrets

- Mots de passe generes aleatoirement (32 caracteres, base64)
- Fichiers `.env` jamais commites (.gitignore)
- Secrets CI/CD dans GitHub Secrets
- Certificats SSL montes en volume `:ro`

### Recommandations restantes

- Restreindre SSH par cle publique uniquement (desactiver PasswordAuthentication)
- Limiter SSH a une liste d'IP autorisees
- Configurer Let's Encrypt (remplacement certificats auto-signes)
- Activer unattended-upgrades pour les mises a jour de securite

## CI/CD (GitHub Actions)

### ci.yml (push main + PR)

1. **Lint & Security** — ruff check/format + bandit
2. **Validate XML & YAML** — xmllint + yaml.safe_load
3. **Docker Build** — build test (push: false)
4. **Odoo Tests** — clone Odoo 19 source (cache), auto-detect modules, `--test-enable`

### build-push.yml (push main + tags)

Build et push vers GHCR (`ghcr.io/isicn/isic-v1`).
Tags : `latest` (main), `sha-XXXXXX`, semver (`v1.0.0` → `1.0.0` + `1.0`).

### deploy.yml (workflow_dispatch)

Deploy manuel avec choix environnement (staging/production) et tag image.
- `-V` (`--renew-anon-volumes`) pour rafraichir `/mnt/extra-addons` (volume anonyme de l'image base)
- Staging deploye d'abord, health check 30s
- Production apres staging OK, backup pre-deploy, health check 45s
- Rollback automatique si health check echoue
- Apres deploy, installer/mettre a jour les modules via SSH : `docker exec <odoo> odoo -d <db> -i/-u <module> --stop-after-init --no-http` puis `docker restart <odoo>`

## Hierarchie pedagogique (modele LMD)

Reference pour le developpement des modules metier :

```
isic.cycle           (Licence, Master, Doctorat)
  └── isic.filiere   (ex: Informatique, Communication, Journalisme)
       └── isic.vdi  (Version de Diplome)
            └── isic.vet  (Version d'Etape = niveau: 1A, 2A, 3A)
                 └── isic.ue   (Unite d'Enseignement, credits ECTS)
                      └── isic.elp  (Element Pedagogique: CM, TD, TP)
```

## Modules deployes

| Module | Description | Status |
|--------|-------------|--------|
| `isic_theme` | Branding ISIC + look enterprise-like (MuK backend) | Installe (dev + staging) |
| `dms` | OCA Document Management System (migre 18→19, 64/64 tests) | Migre, pret |
| `dms_field` | OCA DMS Field — vues DMS embarquees dans les fiches (migre 18→19, 14/14 tests) | Migre, pret |

### isic_theme — Details techniques

Theme CSS/SCSS pur (zero JavaScript) qui transforme Odoo 19 Community en look enterprise.

- **Depends**: `web`, `muk_web_theme` (CE, dans `third-party/`)
- **Assets**: SCSS injecte apres `muk_web_colors` pour override garanti
- **Post-init hook**: Ecrit le nom + logo ISIC sur `base.main_company`
- **Audit securite**: PASS (zero XSS, zero CDN externe, zero credentials exposees)

Fichiers cles :
- `primary_variables.scss` — Override couleurs Odoo ($o-brand-primary, $o-community-color, etc.) + variables composant (border-radius, navbar height, favorite color)
- `backend.scss` — 26 sections (A-Z) : navbar gradient, control panel shadow, form sheet shadow, list headers uppercase, kanban hover lift, searchbar arrondie, dropdowns, boutons, sidebar MuK, home menu, chatter, modals, tooltips, scrollbar fin, transitions
- `login.scss` — Page login premium : gradient bleu fonce, carte centree avec ombre, logo dans pill blanc, accent or, responsive mobile
- `webclient_templates.xml` — Favicon, titre, theme-color, apple-touch-icon, redesign login page
- `static/src/fonts/` — Inter (Regular, Medium, SemiBold, Bold) en woff2 self-hosted
- `static/src/img/` — `isic_logo.png`, `isic_favicon.ico`, `isic_icon_ios.png`

Palette :
| Token | Hex | Usage |
|-------|-----|-------|
| Primary (Deep Blue) | `#1B3A5C` | Navbar, boutons, brand |
| Primary Hover | `#152E4A` | Hover states |
| Accent (Gold) | `#D4A843` | Badges, favoris, loading, navbar badges |
| Link Blue | `#1B4F8C` | Liens |
| Gray Secondary | `#6B7B8D` | Texte secondaire |
| Light BG | `#F0F2F5` | Fonds, webclient bg |

## Cahier des charges (CPS AO N 03/SG/SAF/2025)

Appel d'offres ouvert international pour la conception et le developpement d'une plateforme digitale integree des processus administratifs et d'une plateforme e-learning pour l'ISIC Rabat.

### Decoupage du projet

| Partie | Description | Delai | Paiement |
|--------|-------------|-------|----------|
| **Partie 1** | Cadrage, deploiement socle ERP + Portail Intranet Collaboratif | **3 mois** | 30% |
| **Partie 2** | Modules metiers : Scolarite, RH, GEC (courrier) | 8 mois | 45% (25% + 20%) |
| **Partie 3** | Plateforme e-learning LMS + 3 cours en ligne | 4 mois | 25% |

Delai global : 18 mois. Parties 2 et 3 en parallele apres validation Partie 1.

### Exigences techniques CPS

- 100% open source, full web, on-premise, PostgreSQL
- 50 utilisateurs admin + 500 etudiants simultanes, temps de reponse < 3s
- Support multilingue FR + AR (RTL), responsive, mode sombre
- API REST, SSO, LDAP/AD (quand disponible), MFA
- Workflows configurables, GED, reporting, chat integre
- 2 serveurs physiques fournis : 128 Go RAM, 24 To SAS chacun (rackables)

### Etat de l'existant ISIC

- **Pas de LDAP/AD** : Aucun annuaire centralise en place. Authentification locale Odoo en Partie 1
- **SSO** : Non disponible actuellement. A implementer apres mise en place d'un annuaire
- **SI existant** : Document detaille a venir (fourni par le MOA)

### Mapping CPS → Odoo 19

| Exigence CPS | Notre reponse | Status |
|---|---|---|
| ERP 100% web, open source | Odoo 19 CE | FAIT |
| Framework MVC Python | Odoo ORM + controllers | FAIT |
| PostgreSQL | PostgreSQL 16 (Docker) | FAIT |
| On-premise + Docker | VPS OVH → Migration serveurs ISIC | FAIT (VPS), A FAIRE (migration) |
| HTTPS/SSL | Nginx reverse proxy | FAIT |
| API REST | JSON-RPC natif + module isic_api | A FAIRE |
| WebSocket / Long-polling | Odoo gevent | FAIT |
| LDAP/AD | Module auth_ldap (quand AD disponible) | REPORTE |
| SSO | Module SSO (apres LDAP) | REPORTE |
| Support RTL (arabe) | Odoo i18n natif + pack ar_MA | A CONFIGURER |
| GED / Documents | Module isic_ged | A DEVELOPPER |
| Workflows | isic_approvals | A DEVELOPPER |
| Reporting / Dashboards | Odoo pivot, graph + isic_portal | A DEVELOPPER |
| Chat integre | Odoo Discuss (core) | NATIF |
| Sauvegarde automatisee | Service backup Docker (cron 2h) | FAIT |

## Plan Partie 1 — Socle ERP + Portail Intranet (3 mois)

### Mois 1 : Cadrage, infrastructure, socle ERP
- S1 : Kick-off, collecte documents MOA, acces serveurs
- S2 : PAQ, planning, installation OS + Docker serveurs prod
- S3 : Deploiement Odoo 19 prod, SSL, DNS, staging
- S4 : isic_base, modules core (mail, calendar, project), import utilisateurs

### Mois 2 : Portail Intranet et modules fonctionnels
- S5 : isic_portal (dashboards par profil, page accueil)
- S6 : isic_ged (documents, tags, versionning, recherche)
- S7 : isic_approvals + isic_demandes (workflows, formulaires)
- S8 : isic_api, integration PMB, multilingue FR/AR, demo Mois 2

### Mois 3 : Recette, formation, mise en production
- S9 : Tests unitaires, integration, performance, securite
- S10 : Recette MOA (cahier de recette, PV, corrections)
- S11 : Formation administrateurs (2j) + utilisateurs (2j) + manuels
- S12 : Mise en production, monitoring, transfert, PV reception

### Modules Partie 1

| Module | Semaine | Description |
|--------|---------|-------------|
| `isic_base` | S4 | Socle : groupes securite, annee academique, parametres, menus |
| `isic_portal` | S5 | Portail intranet : dashboards, widgets, profils |
| `isic_ged` | S6 | GED : documents, tags, versionning, recherche full-text |
| `isic_approvals` | S7 | Workflows d'approbation multi-niveaux generiques |
| `isic_demandes` | S7 | Formulaires demandes internes (conge, mission, attestation) |
| `isic_api` | S8 | API REST endpoints, connecteur PMB |

## Modules a developper (roadmap complete)

### Partie 1 — Socle + Portail (3 mois)

| Module | Description | Priorite |
|--------|-------------|----------|
| `isic_base` | Module de base ISIC, dependance commune | P0 |
| `isic_portal` | Portail intranet, dashboards par profil | P0 |
| `isic_ged` | GED : documents, tags, recherche | P1 |
| `isic_approvals` | Workflow d'approbations generiques | P1 |
| `isic_demandes` | Formulaires demandes internes | P1 |
| `isic_api` | API REST, interoperabilite PMB | P2 |

### Partie 2 — Modules metiers (8 mois)

| Module | Description | Priorite |
|--------|-------------|----------|
| `referentiel` | Cycles, filieres, VDI, VET, UE, ELP | P0 |
| `scolarite` | Inscriptions, etudiants, groupes, annees academiques | P0 |
| `admission` | Campagnes, candidatures, scoring, preselection | P1 |
| `examen` | Sessions d'examen, epreuves, notes, deliberations | P1 |
| `modelisation` | Emplois du temps, seances, creneaux | P1 |
| `stage` | Stages, conventions, soutenances | P2 |
| `partenariat` | Conventions de partenariat | P2 |
| `isic_rh` | Gestion RH : conges, missions, dossier personnel | P0 |
| `isic_gec` | Gestion electronique du courrier | P1 |
| `isic_rfid` | Pointage kiosk RFID | P3 |

### Partie 3 — E-learning (4 mois)

| Module | Description | Priorite |
|--------|-------------|----------|
| `isic_lms` | Integration LMS (Moodle ou equivalent) | P0 |

## Modeles de donnees principaux (reference)

- `isic.etudiant` — matricule, nom, prenom, cin, cne, filiere_id, niveau, state (pre_inscrit/inscrit/diplome)
- `isic.inscription` — liaison etudiant/annee/filiere/VET, state (draft/en_attente/validee)
- `isic.note` — epreuve_id, etudiant_id, note/20, note_rattrapage, note_finale (compute)
- `isic.note.ue` — Vue SQL: moyenne ponderee par UE, credits acquis
- `isic.session.examen` — code, semestre (S1/S2), type (normale/rattrapage), state
- `isic.epreuve` — session_id, elp_id, type_epreuve
- `isic.candidature` — campagne_id, filiere_id, score_dossier, note_entretien, score_final (60/40)
- `isic.stage` — etudiant_id, sujet, notes (entreprise 30% + rapport 30% + soutenance 40%)
- `isic.presence` — seance_id, etudiant_id, state (present/retard/absent/justifie)
- `isic.annee.academique` — is_current, inscription_ouverte
- `isic.filiere` — code, cycle_id, capacite, state (draft/accreditee/suspendue)
- `isic.salle` — code, type_salle, capacite, equipement_ids
- `hr.employee` (is_enseignant=True) — grade, specialite, volume_horaire

## Git

- Branche principale : `main`
- Convention de commits : `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
- **JAMAIS de `Co-Authored-By`** dans les messages de commit
- Auteur : Dev Team <isicnumerique@gmail.com>
- Repo GitHub : `isicn/isic-v1` (prive)

## Historique des travaux

### Session 1 — Fevrier 2026 (Infrastructure from scratch)

1. **Repo isic-v1 cree** — 18 fichiers, architecture Docker multi-env, CI/CD GitHub Actions
2. **Dockerfile** — Image `odoo:19.0` + deps systeme + pip `--break-system-packages` + chown permissions
3. **Entrypoint dynamique** — Generation `odoo.conf` depuis env vars, blocs conditionnels (SMTP, Redis, dev_mode, addons_path)
4. **Fix `gevent_port`** — `longpolling_port` renomme en Odoo 19
5. **Fix `addons_path` conditionnel** — N'inclure `/mnt/extra-addons` que s'il contient des modules
6. **Fix SMTP/dev_mode conditionnels** — Eviter `False` sur des options string
7. **Fix PgBouncer** — Image `1.23.1` introuvable → `latest`, `DATABASE_URL` → `DB_HOST` wildcard
8. **Odoo connecte directement aux DB** — Bypass PgBouncer (SCRAM-SHA-256 incompatible en wildcard)
9. **Fix backup mount path** — `./scripts/backup.sh` → `../scripts/backup.sh` (relatif au compose)
10. **VPS deploye** — 7 services actifs, DB initialisees, health checks OK
11. **Nginx HTTPS** — Certificats auto-signes, dual-domain, rate limiting, headers securite
12. **UFW** — deny incoming, allow 22/80/443
13. **fail2ban** — Protection SSH brute force (3 echecs → ban 1h), 4 IP bannies immediatement
14. **Hosts locaux** — `mon.isic.ac.ma` et `staging.isic.ac.ma` → 51.178.47.204 dans `/etc/hosts`
15. **Document DOCX** — `ISIC_Deploiement_Environnements.docx` genere (16 sections, destine au MOA)

### Session 2 — Fevrier 2026 (isic_theme — Enterprise-like branding)

1. **isic_theme module cree** — Branding ISIC complet (couleurs, polices Inter, favicon, logo, titre)
2. **Integration MuK Web Theme (CE)** — Dependance `muk_web_theme` (Community, `excludes: ['web_enterprise']`), SCSS positionne apres `muk_web_colors` via `("after", ...)` pour override garanti
3. **Primary variables** — Override couleurs Odoo ($o-brand-primary, $o-community-color, etc.) + variables composant (border-radius, navbar, favorite color en or)
4. **Backend SCSS (26 sections A-Z)** — Navbar gradient + shadow, control panel shadow, form sheet shadow/radius, list headers uppercase, kanban hover lift, searchbar arrondie, notebook tabs, dropdowns, boutons avec transitions, stat buttons, sidebar MuK avec accent or, home menu gradient, many2one, toggle switches, tags/badges, chatter, action manager fade-in, settings, calendar/pivot/graph, scrollbar fin, links, loading indicator or, modals, tooltips, accent utilities
5. **Login page premium** — Gradient bleu fonce, carte centree avec ombre, logo dans pill blanc avec hover, accent or sous titre, form inputs styles, responsive mobile
6. **Post-init hook** — Ecrit nom "ISIC" + logo PNG sur `base.main_company`
7. **Fix `t-esc` → `t-out`** — Attribut deprecie en Odoo 19
8. **Fix navbar CSS custom properties** — `--NavBar-entry-backgroundColor` pour compatibilite avec les selectors core Odoo 19
9. **Suppression form width vars** — `$o-form-renderer-max-width` et `$o-form-view-sheet-max-width` retires (conflit MuK)
10. **Ruff lint ignore third-party** — `pyproject.toml` ignore ALL rules pour `**/third-party/**`
11. **Audit securite** — PASS complet : zero XSS, zero CDN, zero credentials, zero t-raw, CSP preservee
12. **Remplacement muk_web_enterprise_theme → muk_web_theme** — L'ancien module (EE) necessite `web_enterprise` absent en CE. Remplace par `muk_web_theme` v19.0.1.4.2 (CE, memes deps)
13. **Organisation third-party/** — 7 modules MuK deplaces dans `custom-addons/third-party/`, separation code ISIC / code tiers
14. **Entrypoint addons_path** — Boucle auto-detection : scanne `/mnt/extra-addons` et `/mnt/extra-addons/third-party` pour construire addons_path dynamiquement
15. **Docker-compose dev** — Montage `entrypoint.sh` en volume `:ro` pour live reload sans rebuild image
16. **Fix deploy.yml** — Suppression `script_stop` (deprecie dans `appleboy/ssh-action@v1`)
17. **Secrets GitHub** — `VPS4_HOST`, `VPS4_USER`, `VPS4_SSH_KEY` configures via `gh secret set`
18. **Deploy staging** — Workflow deploy OK en 48s apres fix secrets + script_stop
19. **Nettoyage DB orphelins muk_web_enterprise_theme** — Vues, champs, ir_model_data restes en DB apres desinstallation causaient `OwlError: theme_color_appbar_text_light field is undefined`. Supprime : 3 ir_ui_view, 10 ir_model_fields (_light/_dark), 24 ir_model_data, 1 ir_module_module
20. **Fix volume anonyme /mnt/extra-addons** — Image base `odoo:19.0` declare `VOLUME /mnt/extra-addons`, Docker persiste un volume anonyme vide a travers les redeploys. Fix : `-V` (`--renew-anon-volumes`) dans `deploy.yml`
21. **Fix ruff exclude third-party** — `pyproject.toml` avait `per-file-ignores` pour le lint mais pas d'exclusion globale pour le format. Ajout `exclude = ["custom-addons/third-party"]` dans `[tool.ruff]`
22. **Installation modules staging** — 35 modules installes sur staging via `docker exec odoo -d isic_staging -i isic_theme --stop-after-init --no-http`

### Session 4 — Fevrier 2026 (Deploiement VPS-3 Auth Stack)

1. **Fix HSTS/OCSP VPS-4** — HSTS bloquait l'acces navigateur avec certificats auto-signes (pas de bouton "Continuer"). Commente HSTS + OCSP dans `vps4.conf`, vider cache HSTS Chrome via `chrome://net-internals/#hsts`
2. **Fix http2 directive** — `listen 443 ssl http2` deprecie dans Nginx moderne. Remplace par `listen 443 ssl` + `http2 on` (VPS-4 + VPS-3)
3. **Fix CI hashFiles()** — `hashFiles()` non disponible dans `jobs.<id>.if` (seulement dans steps). Supprime le guard redondant dans `ci.yml`
4. **VPS-3 provisionne** — Ubuntu 24.10, 22 GB RAM, 8 vCPU, IP 51.255.200.172
5. **Docker installe sur VPS-3** — Docker 28.4.0 + Compose 2.39.2 (fix repos Ubuntu 24.10 → old-releases)
6. **UFW + fail2ban VPS-3** — 22/80/443 + 1389 (VPS-4 only), fail2ban SSH (3 IPs bannies immediatement)
7. **Fichiers auth copies dans isic-v1** — docker-compose.auth-vps.yml, nginx/auth.conf, cas/ (16 fichiers), ldap/ (2 fichiers), init-ldap-vps.sh, .env.vps3.template
8. **LDAP deploye** — OpenLDAP 1.5.0, base DN dc=isic,dc=ac,dc=ma, overlays memberOf + refint
9. **LDAP initialise** — 8 utilisateurs (5 staff + 3 etudiants), 4 groupes, 1 compte technique (odoo_bind)
10. **CAS deploye** — Image custom build (Gradle LDAP JARs + WAR overlay + branding ISIC), page login OK
11. **Nginx VPS-3** — Reverse proxy auth.isic.ac.ma + ldap.isic.ac.ma, certificats auto-signes
12. **Documentation DOCX** — `docs/ISIC_Deploiement_VPS3_Auth.docx` genere (15 sections)
13. **CLAUDE.md mis a jour** — Section VPS-3 complete, securite 2 VPS, historique session 4

### Session 3 — Fevrier 2026 (Agents + Analyse CPS)

1. **Nettoyage DB muk_web_enterprise_theme** — Suppression orphelins en DB (3 views, 10 fields, 24 data, 1 module) causant OwlError
2. **Fix volume anonyme /mnt/extra-addons** — `-V` dans deploy.yml pour renouveler volumes anonymes
3. **Fix ruff exclude third-party** — `exclude` dans `[tool.ruff]` pour lint + format
4. **Installation modules staging** — 35 modules installes, isic_theme fonctionnel
5. **Migration commands → skills** — 3 commands migres vers 7 skills dans `.claude/skills/`
6. **Nouveaux agents** — /deploy, /test, /db-ops, /scaffold crees
7. **Hook third-party read-only** — PreToolUse bloque l'ecriture dans `third-party/`
8. **Analyse CPS** — AO N 03/SG/SAF/2025 decortique, mapping vers Odoo 19
9. **Plan Partie 1** — Planning 3 mois detaille (12 semaines), 6 modules, 16 livrables
10. **Questionnaire MOA** — Document exhaustif de collecte (18 sections, 10 documents bloquants, 10 questions)
11. **Constat : pas de LDAP/AD** — L'ISIC ne dispose d'aucun annuaire centralise. Auth locale Odoo en Partie 1

### Session 5 — Fevrier 2026 (Migration dms_field Odoo 18 → 19)

1. **Version bump** — `__manifest__.py` version `18.0.1.1.2` → `19.0.1.0.0`
2. **Suppression `auto_join=True`** — Retire du champ `dms_directory_ids` dans `dms_field_mixin.py` (deprecie en Odoo 19)
3. **`t-esc` → `t-out`** — 6 occurrences remplacees dans `dms_list_renderer.xml` (OWL template)
4. **Rewrite `_search_parents()`** — Methode `dms_directory.py` reecrite : suppression `_where_calc`, `_apply_ir_rules`, `query.from_clause`, `query.where_clause` (API ORM supprimee en Odoo 19). Remplace par ORM pur (`self.search()`)
5. **Suppression import `odoo.osv.expression`** — Module deprecie en Odoo 19 (`odoo.fields.Domain`), `expression.is_false()` remplace par logique ORM simple
6. **Fix `res.groups` champ `users` → `user_ids`** — Renomme en Odoo 19, corrige dans les tests
7. **Fix `fields.first()` → `recordset[:1]`** — Fonction utilitaire supprimee en Odoo 19, 2 occurrences dans les tests
8. **Remplacement demo data par fixtures de test** — `env.ref("dms_field.field_template_partner")` remplace par creation explicite (storage, access group, template, directory) car demo data non charge pendant les tests Odoo 19
9. **Fix recursion infinie `_with_parent` tests** — Ajout `storage_root_directory` separe pour eviter reference circulaire quand `parent_directory_id` pointe vers le propre repertoire du template
10. **14/14 tests passing** — Tous les tests `dms_field` passent sans erreur ni failure
11. **Nettoyage 23 DB de test** — Bases temporaires `test_dms_field_*` supprimees apres validation

## Documents de reference projet

| Document | Chemin | Description |
|----------|--------|-------------|
| Questionnaire MOA Partie 1 | `docs/MOA_Questionnaire_Partie1.md` | Collecte exhaustive documents/donnees a demander au MOA |
| Planning Partie 1 | `docs/Planning_Partie1.md` | Planning detaille 3 mois (12 semaines) |
| Document deploiement VPS-4 | `ISIC_Deploiement_Environnements.docx` | Document deploiement VPS-4 pour le MOA (hors Git) |
| Document deploiement VPS-3 | `docs/ISIC_Deploiement_VPS3_Auth.docx` | Document deploiement auth stack pour le MOA |

## Points d'attention techniques

### Odoo 19

- **Template inheritance** : `-u` ne change PAS le `inherit_id` d'une vue existante. Supprimer l'ancienne vue en DB + `ir_model_data` puis relancer `-u`
- **View inheritance xpath** : L'attribut `string` n'est PAS autorise comme selecteur (`View inheritance may not use attribute 'string' as a selector`). Utiliser `name`, `id`, ou un selecteur de balise/position
- **Duplicate field labels** : Deux champs du meme modele avec le meme `string` generent un WARNING
- **Kanban `<i>` tags accessibilite** : Les `<i>` avec classes FA doivent avoir un attribut `title`
- **ORM registry et serveur long-running** : `-u module --stop-after-init` ecrit en DB mais un serveur deja demarre ne charge PAS les nouvelles classes. Toujours redemarrer apres l'ajout d'un nouveau modele
- **Post-init hook** : Declare via `'post_init_hook': 'fn_name'` dans `__manifest__.py`, la fonction dans `__init__.py` recoit `env` comme argument (pas `cr, registry`)
- **noupdate records** : Les records `noupdate="1"` ne sont pas mis a jour par XML. Utiliser `<function model="..." name="write">` pour forcer via ORM
- **CSS Grid vs Flexbox pour sidebar** : Flexbox avec `flex-wrap` fait descendre la sidebar. Utiliser CSS Grid avec `grid-template-columns`
- **SCSS asset ordering avec MuK** : Utiliser `("after", "muk_web_colors/static/src/scss/colors_light.scss", ...)` au lieu de `"prepend"` pour s'assurer que les variables ISIC overrident MuK
- **Navbar CSS custom properties Odoo 19** : Le core `navbar.scss` utilise `--NavBar-entry-backgroundColor`, `--NavBar-entry-backgroundColor--hover`, `--NavBar-entry-backgroundColor--active`, `--NavBar-entry-borderColor-active`. Les definir dans `.o_main_navbar` pour controler hover/focus/active
- **`t-esc` deprecie en Odoo 19** : Utiliser `t-out` a la place. `t-esc` fonctionne encore mais genere des warnings
- **`$o-form-renderer-max-width` / `$o-form-view-sheet-max-width`** : Ces variables existent dans Odoo mais entrent en conflit avec MuK qui gere sa propre largeur de formulaire. Ne pas les overrider quand MuK est installe
- **`muk_web_theme` vs `muk_web_enterprise_theme`** : Deux modules distincts dans `muk-it/odoo-modules` (branche 19.0). `muk_web_theme` = CE (`excludes: ['web_enterprise']`), `muk_web_enterprise_theme` = EE (`depends: ['web_enterprise']`). Memes 6 deps MuK. Toujours utiliser `muk_web_theme` avec l'image Docker `odoo:19.0` (CE)
- **Module orphelin en DB** : Quand un module installe est supprime du disque, Odoo log `ERROR: Some modules are not loaded`. Corriger via shell : `env['ir.module.module'].search([('name','=','nom')]).write({'state':'uninstalled'})` + `env.cr.commit()`. En plus du state, il faut supprimer les `ir_ui_view`, `ir_model_fields` et `ir_model_data` orphelins sinon les vues qui referencent des champs inexistants provoquent des `OwlError` cote client
- **Addons path et sous-repertoires** : Odoo ne scanne PAS recursivement. `custom-addons/third-party/` doit etre ajoute explicitement a `addons_path`. L'entrypoint utilise une boucle `for dir in ... ; do find ... done`
- **`gevent_port`** : Remplace `longpolling_port` en Odoo 19. L'ancienne option genere un WARNING
- **Config string options** : Ne pas mettre `False` comme valeur par defaut pour `smtp_server`, `smtp_user`, `dev_mode` — ce sont des options string, pas boolean. Utiliser des blocs conditionnels
- **`auto_join=True` deprecie en Odoo 19** : Le parametre `auto_join` sur les champs `One2many`/`Many2many` est deprecie et genere une erreur. Le supprimer lors des migrations
- **`res.groups` champ `users` → `user_ids`** : En Odoo 19, le champ Many2many entre `res.groups` et `res.users` est renomme de `users` a `user_ids`. Cote `res.users`, le champ est `group_ids` (pas `groups_id`)
- **`fields.first()` supprime en Odoo 19** : La fonction utilitaire `odoo.fields.first(recordset)` n'existe plus. Utiliser `recordset[:1]` a la place
- **`_where_calc` / `_apply_ir_rules` supprimes en Odoo 19** : L'API ORM bas niveau (`_where_calc`, `query.from_clause`, `query.where_clause`, `_apply_ir_rules`) a ete reecrite. Utiliser `self.search(domain)` ou `self._search(domain)` qui retournent des Query objects compatibles Odoo 19. Les regles d'acces sont appliquees automatiquement par `search()`
- **`odoo.osv.expression` deprecie en Odoo 19** : Remplace par `odoo.fields.Domain`. L'import `from odoo.osv.expression import ...` genere un `DeprecationWarning`
- **Demo data non charge en mode test Odoo 19** : Les fichiers declares dans `"demo": [...]` du manifest ne sont pas charges lors de `-i module --test-enable`. Les tests doivent creer leurs propres fixtures dans `setUpClass` au lieu de dependre de `env.ref()` vers des records demo

### Docker / Infrastructure

- **`--break-system-packages`** : Requis pour `pip3 install` dans l'image officielle `odoo:19.0` (Python system-managed)
- **`chown` dans Dockerfile** : `/var/lib/odoo` et `/mnt/extra-addons` doivent appartenir a `odoo:odoo`
- **Port 5434** : Le port DB dev est `5434` (pas `5432`) pour eviter conflit avec PostgreSQL local
- **PgBouncer + SCRAM-SHA-256** : PostgreSQL 16 utilise SCRAM par defaut. PgBouncer en mode wildcard (`DB_HOST`) ne gere pas bien l'auth SCRAM. Connexion directe aux DB en attendant
- **PgBouncer mode session vs transaction** : Odoo cron utilise `SAVEPOINT`, `SET`, curseurs longue duree. Toujours `session` mode
- **PgBouncer IGNORE_STARTUP_PARAMETERS** : Odoo envoie `extra_float_digits` et `search_path` au demarrage. Les lister dans `IGNORE_STARTUP_PARAMETERS`
- **OCSP stapling et chain.pem** : `ssl_trusted_certificate` pointe vers le certificat intermediaire seul (pas fullchain). Sans `chain.pem`, `ssl_stapling_verify` echoue silencieusement
- **Backup direct vs PgBouncer** : `pg_dump` doit se connecter directement a `db-prod` (pas via `pgbouncer-prod`)
- **Backup mount path** : Le compose VPS4 est dans `docker/`, donc les volumes relatifs au repo root utilisent `../` (ex: `../scripts/backup.sh:/backup.sh:ro`)
- **Docker log rotation json-file** : `max-size`/`max-file` s'appliquent au stdout/stderr. Les logs ecrits sur disque necessitent logrotate en complement
- **Entrypoint monte en volume dev** : `docker-compose.yml` monte `docker/entrypoint.sh:/entrypoint-isic.sh:ro` pour editer l'entrypoint sans rebuild. `docker compose restart` ne relit PAS les volumes — il faut `docker compose down && docker compose up -d`
- **`appleboy/ssh-action@v1` — `script_stop` deprecie** : Le parametre `script_stop` n'est plus accepte. Utiliser `set -e` dans le script a la place
- **GitHub Secrets** : `VPS4_HOST` (`51.178.47.204`), `VPS4_USER` (`ubuntu`), `VPS4_SSH_KEY` (cle privee ed25519)
- **Volume anonyme `VOLUME /mnt/extra-addons`** : L'image base `odoo:19.0` declare ce VOLUME. Docker cree un volume anonyme au premier `up` et le reutilise meme quand l'image change, masquant les custom-addons bakes dans la nouvelle image. Fix : `docker compose up -d -V` (`--renew-anon-volumes`) pour forcer un volume frais a chaque deploy
- **`docker exec` + `--no-http`** : Pour installer/mettre a jour des modules dans un conteneur Odoo deja demarre, utiliser `--no-http` pour eviter le conflit de port (`OSError: Address already in use`). Pas besoin de `--stop-after-init` seul car il tente aussi de lier le port
- **Ruff `exclude` vs `per-file-ignores`** : `per-file-ignores` n'affecte que le lint (ruff check), pas le format (ruff format). Pour exclure completement un repertoire, utiliser `exclude` dans `[tool.ruff]`
- **Redis session store** : Conditionnel dans `entrypoint.sh` (active si `REDIS_HOST` defini). Prefixes isoles pour prod/staging
- **Init DB apres premier deploiement** : La DB creee par PostgreSQL (`POSTGRES_DB`) n'a pas le schema Odoo. Il faut `docker exec <odoo> odoo -d <db> -i base --stop-after-init` pour initialiser
- **Ubuntu 24.10 apt repos** : Les repos Ubuntu 24.10 (Oracular) peuvent expirer. Utiliser `old-releases.ubuntu.com` si `apt-get update` echoue avec 404. Docker installe depuis le repo `noble` (24.04 LTS)
- **HSTS + certificats auto-signes** : `Strict-Transport-Security` avec `max-age=63072000` empeche Chrome de contourner l'avertissement certificat (pas de bouton "Continuer"). Commenter HSTS tant que Let's Encrypt n'est pas configure. Si deja cache, vider via `chrome://net-internals/#hsts` → Delete domain
- **`listen 443 ssl http2` deprecie** : Nginx moderne exige `listen 443 ssl;` + `http2 on;` sur une ligne separee
- **CAS Apereo startup lent** : Le conteneur CAS met ~2 minutes a demarrer (JVM + war deploy). Le healthcheck a un `start_period: 120s` pour eviter les faux positifs
- **CAS image build Gradle** : Le build telecharge les JARs LDAP via Gradle, puis les injecte dans le WAR CAS. Necessite un acces Internet pendant le build
- **LDAP overlays memberOf/refint** : Doivent etre actives APRES le premier demarrage du conteneur (via `ldapmodify`). Le script `init-ldap-vps.sh` gere cela automatiquement
- **LDAP port 1389 et UFW** : Le port LDAP est expose sur le host en 1389 (pas 389 pour eviter conflit). UFW ne filtre que le trafic entrant sur les ports hote, pas le trafic inter-conteneurs Docker

## Configuration Tech Lead Claude Code

### Architecture des roles

```
Human Lead (vous)
  │
  └── Claude Tech Lead
       ├── /architect  — Conception (lecture seule)
       ├── /implement  — Code production (ecriture custom-addons/)
       ├── /review     — Revue de code (lecture seule)
       ├── /scaffold   — Creation structure module
       ├── /test       — Pipeline de test complet
       ├── /deploy     — Deploiement staging/production
       └── /db-ops     — Operations base de donnees
```

### Cycle de travail recommande

```
1. /architect <module>     → Document d'architecture
2. Validation humaine      → Approbation / ajustements
3. /scaffold <module>      → Structure du module (optionnel)
4. /implement <module>     → Code Odoo qualite production
5. /test <module>          → Lint + XML + tests unitaires + upgrade DB
6. /review [module]        → Rapport de revue (PASS/WARN/FAIL)
7. Iteration si REJETE     → Retour a l'etape 4
8. Commit si APPROUVE      → git add + commit
9. /deploy staging         → Deployer et verifier
10. /deploy production     → Deployer en production
```

### Commandes slash (skills)

| Commande | Role | Acces | Utilisation |
|----------|------|-------|-------------|
| `/architect <desc>` | Architecte | Lecture seule | Concevoir l'architecture d'un module |
| `/implement <desc>` | Implementeur | Ecriture `custom-addons/` | Code Odoo 19 qualite production |
| `/review [module]` | Reviewer | Lecture seule | Revue de code avec verdicts |
| `/scaffold <name>` | Scaffolder | Ecriture `custom-addons/` | Creer la structure d'un module |
| `/test [module]` | Testeur | Lecture + exec | Lint, XML, tests, upgrade DB |
| `/deploy <env> [module]` | Operateur | gh, ssh, docker | Deployer et installer modules |
| `/db-ops <action> [env]` | Operateur DB | docker, psql, ssh | Backup, restore, cleanup, shell |

### Hooks automatiques

| Hook | Declencheur | Action | Comportement |
|------|-------------|--------|-------------|
| Ruff auto-format | PostToolUse (Edit/Write) | `ruff format` + `ruff check --fix` | Formate les .py dans custom-addons/ |
| XML validation | PostToolUse (Write) | `xmllint --noout` | BLOQUE si XML invalide dans custom-addons/ |
| Test failure | PostToolUse (Bash) | Analyse stdout/stderr | Signale ERROR/FAIL/Traceback apres make test |
| Fichiers sensibles | PreToolUse (Edit/Write) | Verifie le chemin | BLOQUE l'ecriture dans .env / credentials / secrets |
| Third-party read-only | PreToolUse (Edit/Write) | Verifie le chemin | BLOQUE l'ecriture dans third-party/ |

### Prerequis outils

- **ruff** : `pip install ruff` (linting + formatting Python)
- **xmllint** : `brew install libxml2` ou `apt install libxml2-utils` (validation XML)
- **jq** : `brew install jq` ou `apt install jq` (parsing JSON pour hooks Bash)

## Fichiers importants

- `docker-compose.yml` — Dev local (Odoo + PostgreSQL + pgAdmin)
- `docker/docker-compose.vps4.yml` — VPS-4 prod+staging (7 services actifs + 2 PgBouncer en reserve)
- `docker/Dockerfile` — Image Odoo custom
- `docker/entrypoint.sh` — Generation odoo.conf dynamique (blocs conditionnels)
- `docker/nginx/vps4.conf` — Reverse proxy VPS-4 dual-domain
- `docker/nginx/auth.conf` — Reverse proxy VPS-3 (CAS + phpLDAPadmin)
- `docker/docker-compose.auth-vps.yml` — Auth stack VPS-3 (4 services)
- `docker/cas/Dockerfile` — Image CAS custom multi-stage
- `docker/cas/config/cas.properties` — Config CAS → LDAP
- `docker/ldap/bootstrap/01-isic-structure.ldif` — Structure annuaire ISIC
- `docker/init-ldap-vps.sh` — Script init LDAP (overlays + donnees)
- `docker/.env.vps3.template` — Template variables VPS-3
- `docker/logrotate/odoo.conf` — Rotation logs
- `.github/workflows/ci.yml` — Pipeline CI
- `.github/workflows/build-push.yml` — Build & push GHCR
- `.github/workflows/deploy.yml` — Deploy avec rollback
- `scripts/backup.sh` — Backup DB
- `scripts/generate_deployment_doc.py` — Generation document DOCX deploiement VPS-4
- `scripts/generate_vps3_doc.py` — Generation document DOCX deploiement VPS-3
- `Makefile` — Commandes projet
- `pyproject.toml` — Config outils qualite
- `.pre-commit-config.yaml` — Hooks pre-commit
- `.env.template` — Variables dev
- `.env.vps4.template` — Variables VPS-4
- `docs/ISIC_Deploiement_VPS3_Auth.docx` — Document deploiement VPS-3 auth pour le MOA
