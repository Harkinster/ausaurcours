# Au SAURcours — Starter Pro (MariaDB + Typesense + FastAPI + Apache)

Ce kit te donne un socle **pro** prêt à déployer :
- **MariaDB** = vérité unique (articles, utilisateurs, catégories, tags)
- **Typesense** = index de recherche (tolérance typo, facettes)
- **FastAPI** = API métier sur `127.0.0.1:8001`
- **Apache** = reverse proxy `/api/` → FastAPI

## 0) Pré-requis (Ubuntu 24.04)
```bash
sudo apt update
sudo apt install -y python3-venv python3-pip mariadb-server unzip curl
# utilitaires (facultatif)
sudo apt install -y jq
```
> Assure-toi qu'Apache est déjà installé et fonctionnel (c'est ton cas).

---

## 1) Créer la base MariaDB et l'utilisateur
```bash
sudo mysql -u root <<'SQL'
CREATE DATABASE IF NOT EXISTS ausaurcours CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'ausaur'@'localhost' IDENTIFIED BY 'CHANGE_ME_STRONG';
GRANT ALL PRIVILEGES ON ausaurcours.* TO 'ausaur'@'localhost';
FLUSH PRIVILEGES;
SQL

# Importer le schéma
mysql -u ausaur -p ausaurcours < /srv/ausaurcours-api/sql/schema.sql
```

---

## 2) Installer Typesense en local (127.0.0.1:8108)
```bash
sudo mkdir -p /srv/typesense/bin /srv/typesense/data
cd /srv/typesense/bin

# Télécharger automatiquement la dernière release (nécessite jq).
curl -s https://api.github.com/repos/typesense/typesense/releases/latest \
  | jq -r '.assets[] | select(.name | test("linux.*amd64|linux.*x86_64")) | .browser_download_url' \
  | head -n1 \
  | xargs -I{} bash -c 'curl -L "{}" -o typesense.tar.gz'

tar -xzf typesense.tar.gz --strip-components=0
chmod +x typesense-server || true

# Génère une clé API (copie-la dans .env plus tard)
openssl rand -hex 32 | tee /srv/typesense/TYPESENSE_API_KEY.txt

# Service systemd
sudo cp /srv/ausaurcours-api/systemd/typesense.service /etc/systemd/system/typesense.service
sudo systemctl daemon-reload
sudo systemctl enable --now typesense
sudo systemctl status typesense --no-pager
```

> Si tu n'as pas `jq`, remplace le bloc `curl ... | jq ...` par un téléchargement manuel
depuis la page Typesense (binaire Linux), puis place `typesense-server` dans `/srv/typesense/bin/`.

---

## 3) Déployer l'API FastAPI
```bash
sudo mkdir -p /srv/ausaurcours-api
sudo rsync -a /mnt/data/ausaurcours_pro_starter/ /srv/ausaurcours-api/

cd /srv/ausaurcours-api
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Prépare ton .env
cp .env.example .env
nano .env  # -> renseigne DB, TYPESENSE_API_KEY (cat /srv/typesense/TYPESENSE_API_KEY.txt), ADMIN_TOKEN
```

Initialiser la collection Typesense (la 1ère fois) :
```bash
source /srv/ausaurcours-api/.venv/bin/activate
python -c "from app.search import ensure_collection; ensure_collection()"
```

Service systemd de l'API :
```bash
sudo cp /srv/ausaurcours-api/systemd/ausaurcours-api.service /etc/systemd/system/ausaurcours-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now ausaurcours-api
sudo systemctl status ausaurcours-api --no-pager
```

Tests rapides :
```bash
curl -s http://127.0.0.1:8001/api/health
```

---

## 4) Config Apache — proxy propre `/api/`
Édite **tes deux vhosts** (80 & 443) pour **ajouter seulement ces lignes** dans le bloc `VirtualHost` :

```
ProxyPass        /api/ http://127.0.0.1:8001/api/
ProxyPassReverse /api/ http://127.0.0.1:8001/api/
RequestHeader set X-Forwarded-Proto "https" env=HTTPS
```

Puis :
```bash
sudo a2enmod proxy proxy_http headers
sudo apache2ctl -t && sudo systemctl reload apache2
```

Smoke tests via domaine :
```bash
curl -s https://ausaurcours.ddns.net/api/health
```

---

## 5) Créer un contenu d'exemple (via Admin Token)
```bash
ADMIN_TOKEN=$(grep ^ADMIN_TOKEN= /srv/ausaurcours-api/.env | cut -d= -f2)

# 1) créer une catégorie
curl -s -X POST https://ausaurcours.ddns.net/api/admin/categories \  -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \  -d '{"name":"Abonnement","slug":"abonnement"}'

# 2) créer un tag
curl -s -X POST https://ausaurcours.ddns.net/api/admin/tags \  -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \  -d '{"name":"abo"}'

# 3) créer un utilisateur (éditeur)
curl -s -X POST https://ausaurcours.ddns.net/api/admin/users \  -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \  -d '{"username":"matthieu","email":"laurens.matthieu@yahoo.fr","role":"editor"}'

# 4) créer un article
curl -s -X POST https://ausaurcours.ddns.net/api/admin/articles \  -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \  -d '{"slug":"abonnement-particulier","title":"Abonnement – Particulier","content":"Étapes : opportunité → saisie complète → DocuSign.","category_slug":"abonnement","tags":["abo"],"author_username":"matthieu"}' | jq .

# 5) rechercher
curl -s "https://ausaurcours.ddns.net/api/search?q=abo" | jq .
```

---

## 6) Sécurité & sauvegardes
- Ne **proxifie pas** Typesense via Apache : il reste en `127.0.0.1:8108`.
- Sauvegardes :
  - MariaDB: `mysqldump ausaurcours > /backup/ausaurcours_$(date +%F).sql`
  - Typesense: l'index est reconstruisible depuis la DB (`/api/search/rebuild` sera fourni).
- Bloque l'accès aux fichiers sensibles dans Apache (ton vhost ne sert que /srv/ausaurcours).

Bonne mise en place !
