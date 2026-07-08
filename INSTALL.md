# Procédure d'installation — poste OL9.6 custom

## 0. Prérequis

- Une VM Oracle Linux 9.6 **cible** (celle qu'on provisionne), installée depuis `OracleLinux-R9-U6-x86_64-dvd.iso`, sans accès internet.
- Une VM Oracle Linux 9.6 **de téléchargement**, installée depuis le **même ISO**, avec accès internet.
  Ne jamais lancer `dnf update` dessus : elle doit rester alignée sur la base de la cible, sinon les paquets récupérés entrent en conflit avec ceux déjà installés (`oraclelinux-release`, `rpm-libs`, `device-mapper`, etc.).
- Le tarball JDK Temurin déjà téléchargé (ex. `8.0.392-tem`), et les `.desktop` déjà prêts.

## 1. Construire le bundle sur la VM de téléchargement

Télécharger les RPM + dépendances réellement nécessaires (jamais `--alldeps`, qui ramène des paquets déjà satisfaits en dernière version distante) :

```bash
sudo dnf download --resolve --destdir=/tmp/newbundle/rpms -x "oraclelinux-release*" \
  wireshark jq xterm inotify-tools gettext java-1.8.0-openjdk-headless
cd /tmp/newbundle/rpms
sha256sum *.rpm > SHA256SUMS
```

Rassembler la structure finale **dans un dossier natif du système de fichiers** (jamais directement sur un partage `/mnt/hgfs/...` : ce type de partage ne supporte pas les liens symboliques, et le JDK en contient) :

```bash
mkdir -p /tmp/newbundle/opt/install
mv /tmp/newbundle/rpms /tmp/newbundle/opt/install/rpms
mkdir -p /tmp/newbundle/opt/install/desktop
cp /chemin/vers/*.desktop /tmp/newbundle/opt/install/desktop/
mkdir -p /tmp/newbundle/opt/install/java
cp -r /chemin/vers/8.0.392-tem /tmp/newbundle/opt/install/java/

tar czf bundle_install.tar.gz -C /tmp/newbundle opt
```

Ne copier que ce fichier `bundle_install.tar.gz` (un seul fichier, pas de dossier avec des symlinks) vers l'endroit partagé avec la VM cible.

## 2. Transférer sur la VM cible

Transférer `bundle_install.tar.gz` et le dossier `scriptInstallApps/` (les `.py` + `config.json`) sur la VM cible.

## 3. Adapter config.json

Éditer `config.json` sur la cible, remplacer les valeurs d'exemple :

```json
{
  "rpm_dir": "/opt/install/rpms",
  "java_src_dir": "/opt/install/java",
  "java_version": "8.0.392-tem",
  "desktop_src_dir": "/opt/install/desktop",
  "gnome_extensions": ["uuid-reel-1@exemple.com", "uuid-reel-2@exemple.com"],
  "opt_app_dirs": ["/opt/nom-app-1", "/opt/nom-app-2"]
}
```

`gnome_extensions` : les vrais UUID des extensions à activer.
`opt_app_dirs` : les vrais dossiers d'applis sous `/opt/` à passer en 755 récursif (dossiers + fichiers).

## 4. Lancer l'installation

Un seul point d'entrée, qui déploie le bundle puis lance tout le reste :

```bash
sudo python3 install.py /chemin/vers/bundle_install.tar.gz
```

Ordre d'exécution :
0. `deploy_bundle.py` : extraction de l'archive, vidage/recopie de `opt/install/{rpms,desktop,java}` (jamais de mélange avec un bundle précédent)
1. Vérification SHA256 puis installation des RPM (`dnf install -y --disablerepo=*`)
2. Déploiement du JDK Temurin dans `/opt/java/<version>`, `JAVA_HOME`/`PATH` via `/etc/profile.d/java.sh`
3. Assouplissement de `/etc/security/pwquality.conf` (minlen=5, reste à 0, usercheck=0 pour autoriser le username comme mot de passe)
4. Prompt interactif pour créer un ou plusieurs comptes locaux (username, mot de passe masqué, changement forcé à la prochaine connexion en option) — pas piloté par `config.json`, pas de mot de passe stocké dans un fichier
5. Copie des `.desktop` vers `/usr/share/applications/` (chmod 644)
6. Activation des extensions GNOME par défaut système (dconf, `/etc/dconf/db/local.d/`)
7. `chmod 755` récursif sur les dossiers `/opt/` listés

(`deploy_bundle.py` et `main.py` restent utilisables séparément si besoin de rejouer une seule étape.)

## 5. Vérifications post-install

```bash
java -version                          # doit pointer sur le Temurin 8.0.392
rpm -q wireshark jq xterm gettext      # paquets bien installés
ls -l /usr/share/applications/*.desktop
dconf read /org/gnome/shell/enabled-extensions
```

## Pièges déjà rencontrés (pour mémoire)

- `sudo cmd > fichier` : la redirection `>` n'est **pas** exécutée par sudo, elle s'exécute avec les droits du shell courant. Utiliser `cmd | sudo tee fichier` à la place.
- `--allowerasing` peut faire proposer à dnf de désinstaller des paquets protégés (`dnf`, `yum`) si le lot de RPM contient des doublons de composants système — signe qu'il faut nettoyer le lot, pas forcer le flag.
- `dnf download --alldeps` ramène des dépendances déjà satisfaites en dernière version du dépôt distant (ex. `oraclelinux-release` qui saute de 9.6 à 9.7/9.8). Toujours `--resolve` seul, avec `-x "oraclelinux-release*"` en filet de sécurité.
- Ne jamais construire/extraire une arborescence avec des liens symboliques (JDK, etc.) directement sur un partage `/mnt/hgfs/...` : ces partages VMware ne supportent pas les symlinks.
