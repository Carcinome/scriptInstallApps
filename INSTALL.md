# Procédure d'installation — poste OL9.6 custom

## 0. Prérequis

- Une VM Oracle Linux 9.6 **cible** (celle qu'on provisionne), installée depuis `OracleLinux-R9-U6-x86_64-dvd.iso`, sans accès internet.
- Une VM Oracle Linux 9.6 **de téléchargement**, installée depuis le **même ISO**, avec accès internet.
  Ne jamais lancer `dnf update` dessus : elle doit rester alignée sur la base de la cible, sinon les paquets récupérés entrent en conflit avec ceux déjà installés (`oraclelinux-release`, `rpm-libs`, `device-mapper`, etc.).
- Le tarball JDK Temurin déjà téléchargé (ex. `8.0.392-tem`), et les `.desktop` déjà prêts.

## 1. Construire le bundle sur la VM de téléchargement

Le bundle contient **deux lots de RPM séparés**, chacun avec son propre `SHA256SUMS` :

- `libreoffice/` : LibreOffice et tout son jeu de dépendances (`--alldeps`), pris **depuis l'ISO d'installation**.
- `rpms/` : le reste (wireshark, jq, xterm, inotify-tools, gettext, java headless), aussi en `--alldeps`, pris depuis l'ISO sauf `inotify-tools` qui vient du dépôt EPEL.

### 1a. Lot LibreOffice (depuis l'ISO, avec `--alldeps`)

On utilise l'ISO comme dépôt local, pas les dépôts en ligne. Raison : les dépôts en ligne OL9 avancent en continu (9.7, 9.8...), alors que la cible est en 9.6. Avec `--alldeps`, ils ramèneraient des versions plus récentes que l'OS de base et on retomberait dans les conflits `dnf` déjà vus. L'ISO contient exactement les versions 9.6, donc `--alldeps` y est sans risque.

```bash
sudo mkdir -p /mnt/iso
sudo mount -o loop,ro /chemin/vers/OracleLinux-R9-U6-x86_64-dvd.iso /mnt/iso

sudo tee /etc/yum.repos.d/iso.repo > /dev/null <<'EOF'
[iso-baseos]
name=OL9.6 ISO BaseOS
baseurl=file:///mnt/iso/BaseOS
enabled=1
gpgcheck=1
gpgkey=file:///mnt/iso/RPM-GPG-KEY-oracle

[iso-appstream]
name=OL9.6 ISO AppStream
baseurl=file:///mnt/iso/AppStream
enabled=1
gpgcheck=1
gpgkey=file:///mnt/iso/RPM-GPG-KEY-oracle
EOF

sudo dnf download --resolve --alldeps --disablerepo='*' --enablerepo='iso-*' \
  --destdir=/tmp/newbundle/libreoffice \
  libreoffice-writer libreoffice-calc libreoffice-impress libreoffice-draw \
  libreoffice-langpack-fr libreoffice-help-fr hunspell-fr hyphen-fr mythes-fr
cd /tmp/newbundle/libreoffice
sha256sum *.rpm | sudo tee SHA256SUMS > /dev/null
```

**Vérification avant d'expédier** (sur cette VM vierge, rien n'est installé) : un essai à blanc doit lister uniquement des paquets à installer, aucune ligne `Removing` ni `Downgrading`.

```bash
sudo dnf install --assumeno --disablerepo='*' /tmp/newbundle/libreoffice/*.rpm
```

### 1b. Lot RPM habituel (`--alldeps`, depuis l'ISO + EPEL seul)

Wireshark, jq, xterm, gettext et java headless sont tous sur l'ISO 9.6. Seul `inotify-tools` n'y est pas : il vient d'EPEL. Pour que `--alldeps` reste sûr, on désactive **tous les dépôts en ligne sauf EPEL** : les dépendances sont alors prises sur l'ISO (versions 9.6), et seul `inotify-tools` (et sa bibliothèque) vient d'EPEL.

D'abord, repérer le nom exact du dépôt EPEL sur la VM :

```bash
dnf repolist --all | grep -i epel
```

Puis (en remplaçant `ol9_developer_EPEL` par le nom affiché ci-dessus) :

```bash
sudo dnf download --resolve --alldeps --disablerepo='*' \
  --enablerepo='iso-*' --enablerepo=ol9_developer_EPEL \
  --destdir=/tmp/newbundle/rpms \
  wireshark jq xterm inotify-tools gettext java-1.8.0-openjdk-headless
cd /tmp/newbundle/rpms
sha256sum *.rpm | sudo tee SHA256SUMS > /dev/null
```

**Vérification avant d'expédier** (sur la VM A vierge) : essai à blanc, aucune ligne `Removing` ni `Downgrading` attendue.

```bash
sudo dnf install --assumeno --disablerepo='*' /tmp/newbundle/rpms/*.rpm
```

### 1c. Assembler et archiver

Rassembler la structure finale **dans un dossier natif du système de fichiers** (jamais directement sur un partage `/mnt/hgfs/...` : ce type de partage ne supporte pas les liens symboliques, et le JDK en contient) :

```bash
mkdir -p /tmp/newbundle/opt/install
mv /tmp/newbundle/libreoffice /tmp/newbundle/opt/install/libreoffice
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
  "libreoffice_rpm_dir": "/opt/install/libreoffice",
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

### Lancer en deux phases (option `--phase`)

Par défaut, `install.py` fait tout d'un coup (`--phase all`). On peut aussi séparer la partie sans interaction de la création de comptes, qui demande quelqu'un devant le clavier :

```bash
sudo python3 install.py /chemin/vers/bundle_install.tar.gz --phase provision
```

Déploie le bundle puis fait toute l'installation **sans poser de question** (LibreOffice, RPM, Java, mots de passe, raccourcis, GNOME, droits).

```bash
sudo python3 install.py /chemin/vers/bundle_install.tar.gz --phase accounts
```

Lance **seulement** la création de comptes, sans toucher au bundle (rien n'est vidé ni recopié).

Ce découpage sert au premier démarrage de l'ISO personnalisée : le reste tourne sans surveillance, et les comptes se créent à la console.

### Poste avec un profil de durcissement (OpenSCAP)

Si la variable d'environnement `OL96_HARDENING_PROFILE` est définie avec un nom de profil (CIS, STIG...), l'étape 4 ci-dessous (assouplissement de `pwquality.conf`) est **sautée** : OpenSCAP a déjà durci ce fichier et l'installeur ne l'écrase pas. Variable absente ou égale à `none` : comportement habituel.

Ordre d'exécution (c'est l'ordre réel de `main.py`) :
0. `deploy_bundle.py` : extraction de l'archive, vidage/recopie de `opt/install/{libreoffice,rpms,desktop,java}` (jamais de mélange avec un bundle précédent)

Puis la partie sans interaction (`--phase provision`) :

1. Vérification SHA256 puis installation de LibreOffice, en premier et dans sa propre transaction `dnf`, avec contrôle final `rpm -q`
2. Vérification SHA256 puis installation des RPM (`dnf install -y --disablerepo=*`)
3. Déploiement du JDK Temurin dans `/opt/java/<version>`, `JAVA_HOME`/`PATH` via `/etc/profile.d/java.sh`
4. Assouplissement de `/etc/security/pwquality.conf` (minlen=5, reste à 0, usercheck=0 pour autoriser le username comme mot de passe), sauf si un profil de durcissement est actif
5. Copie des `.desktop` vers `/usr/share/applications/` (chmod 644)
6. Activation des extensions GNOME par défaut système (dconf, `/etc/dconf/db/local.d/`)
7. `chmod 755` récursif sur les dossiers `/opt/` listés

Enfin la partie interactive (`--phase accounts`) :

8. Prompt pour créer un ou plusieurs comptes locaux (username, mot de passe masqué, changement forcé à la prochaine connexion en option, ajout au groupe `wheel` en option) — pas piloté par `config.json`, pas de mot de passe stocké dans un fichier

(`deploy_bundle.py` et `main.py` restent utilisables séparément si besoin de rejouer une seule étape.)

### Installer LibreOffice seul, hors bundle (poste déjà déployé)

Copier le dossier `libreoffice/` (RPM + `SHA256SUMS`), `libreoffice_setup.py` et `rpm_installer.py` sur le poste, puis :

```bash
sudo python3 libreoffice_setup.py /chemin/vers/libreoffice
```

Ça vérifie les empreintes, lance l'installation `dnf`, puis contrôle avec `rpm -q` que `libreoffice-core`, `-writer`, `-calc` et `-impress` sont bien présents, comme le fait `main.py`. Sans argument, le dossier par défaut est `/opt/install/libreoffice`. (`rpm_installer.py <dossier>` fait la même chose pour n'importe quel autre lot de RPM, mais sans le contrôle final.) Si le poste a reçu avec l'ancien bundle des paquets plus récents que l'ISO (par exemple `tzdata-java` 2026b contre 2025a dans le lot), `install_rpms` ignore automatiquement les fichiers du lot qui rétrograderaient un paquet installé, et affiche une ligne « Ignoré, version plus récente déjà installée ». Cela exige le module Python `rpm`, présent par défaut avec `dnf` sur OL9. Sur un poste déjà déployé, faire quand même d'abord un essai à blanc sur un seul poste (`sudo dnf install --assumeno --disablerepo='*' /chemin/vers/libreoffice/*.rpm`) : le lot vient de l'ISO 9.6 alors que ces postes ont reçu quelques paquets plus récents, il faut s'assurer que `dnf` ne propose aucun `Removing` ni `Downgrading`.

## 5. Vérifications post-install

```bash
java -version                          # doit pointer sur le Temurin 8.0.392
rpm -q wireshark jq xterm gettext      # paquets bien installés
rpm -q libreoffice-writer libreoffice-calc libreoffice-impress   # LibreOffice installé
ls -l /usr/share/applications/*.desktop
dconf read /org/gnome/shell/enabled-extensions
```

## Pièges déjà rencontrés (pour mémoire)

- `sudo cmd > fichier` : la redirection `>` n'est **pas** exécutée par sudo, elle s'exécute avec les droits du shell courant. Utiliser `cmd | sudo tee fichier` à la place.
- `--allowerasing` peut faire proposer à dnf de désinstaller des paquets protégés (`dnf`, `yum`) si le lot de RPM contient des doublons de composants système — signe qu'il faut nettoyer le lot, pas forcer le flag.
- `dnf download --alldeps` ramène des dépendances déjà satisfaites en dernière version du dépôt distant (ex. `oraclelinux-release` qui saute de 9.6 à 9.7/9.8). `--alldeps` n'est sûr que si les dépendances viennent de l'ISO 9.6 elle-même : c'est pourquoi les deux lots sont téléchargés avec les dépôts en ligne `ol9_*` désactivés (`--disablerepo='*'`), seul EPEL restant actif pour `inotify-tools`. Ne **pas** ajouter `-x "oraclelinux-release*"` avec `--alldeps` : la chaîne `glibc` → `basesystem` → `setup` → `system-release` exige ce paquet, et l'exclure fait échouer la résolution (« filtered out by exclude filtering »). Ce n'est pas nécessaire : l'ISO et EPEL ne fournissent que `oraclelinux-release` 9.6, la même version que la cible.
- Un paquet oublié dans le bundle ne se voit pas à l'installation (tout passe) mais sur le terrain. Avant d'expédier, relire la liste des paquets demandés et vérifier avec `rpm -q` sur une VM vierge.
- Ne jamais construire/extraire une arborescence avec des liens symboliques (JDK, etc.) directement sur un partage `/mnt/hgfs/...` : ces partages VMware ne supportent pas les symlinks.
- Penser impérativement à faire un sudo chmod 644 sur le raccourci applicatif dans `/usr/share/application/*.desktop`.