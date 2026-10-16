# scriptInstallApps — installeur de poste Oracle Linux 9.6

Outil 100 % Python (bibliothèque standard uniquement, aucune dépendance à installer) qui prépare un poste de travail OL9.6 à partir d'un OS vierge, **hors ligne** : applications, Java, comptes, raccourcis, extensions GNOME et droits.

## Documentation

| Fichier | Contenu |
|---|---|
| [INSTALL.md](INSTALL.md) | Procédure complète : construire le bundle, le déployer, vérifier, pièges connus |
| [DOCUMENTATION.md](DOCUMENTATION.md) | Référence de chaque fonction : syntaxe, utilité, exemple, erreurs à éviter, pourquoi (aussi en [PDF](DOCUMENTATION.pdf)) |

## Démarrage rapide

Une fois le bundle construit et `config.json` adapté (voir [INSTALL.md](INSTALL.md)), sur le poste cible, depuis le dossier du projet :

```bash
sudo python3 install.py /chemin/vers/bundle_install.tar.gz
```

À lancer **depuis le dossier du projet** : `config.json` est lu par rapport au dossier courant.

## Ce que fait l'installation, dans l'ordre

1. **Déploiement du bundle** : l'archive est extraite et `opt/install/{libreoffice,rpms,desktop,java}` est vidé puis recopié (aucun mélange avec un ancien bundle).
2. **LibreOffice** : vérification SHA256, installation dans sa propre transaction `dnf`, puis contrôle avec `rpm -q`.
3. **RPM habituels** : vérification SHA256, puis `dnf install` sans dépôts distants.
4. **Java** : JDK Temurin copié dans `/opt/java/<version>`, `JAVA_HOME` et `PATH` posés pour tous les comptes.
5. **Politique de mot de passe** : `pwquality.conf` assoupli (voir plus bas pour l'exception OpenSCAP).
6. **Raccourcis** : `.desktop` copiés dans `/usr/share/applications/` (chmod 644).
7. **Extensions GNOME** : activées par défaut pour tous les comptes (dconf).
8. **Droits** : `chmod 755` récursif sur les dossiers `/opt/` listés dans la config.
9. **Comptes** (interactif) : username, mot de passe temporaire, changement forcé à la prochaine connexion, ajout au groupe `wheel`.

## Modes de lancement

`install.py` accepte une option `--phase` pour lancer l'installation en deux moitiés séparées :

| Commande | Effet |
|---|---|
| `sudo python3 install.py bundle.tar.gz` | Tout, dans l'ordre (comportement par défaut, `--phase all`) |
| `sudo python3 install.py bundle.tar.gz --phase provision` | Déploiement + toute la partie sans interaction |
| `sudo python3 install.py bundle.tar.gz --phase accounts` | Seulement la création de comptes (interactive), sans toucher au bundle |

Ce découpage sert au flux de premier démarrage de l'ISO personnalisée, où les comptes se créent à la console pendant que le reste tourne sans surveillance.

### Profil de durcissement (OpenSCAP)

Si la variable d'environnement `OL96_HARDENING_PROFILE` est définie et différente de `none`, l'étape « politique de mot de passe » est **sautée** : un profil CIS/STIG a déjà durci `pwquality.conf` et l'installeur ne l'écrase pas. Absente ou égale à `none`, le comportement est inchangé.

## Scripts utilisables seuls

Chaque brique peut tourner indépendamment, sans passer par `install.py` :

| Commande | Usage |
|---|---|
| `sudo python3 accounts.py` | Créer un compte (prompts interactifs) |
| `sudo python3 libreoffice_setup.py [dossier]` | Installer LibreOffice seul, par exemple sur un poste déjà déployé |
| `sudo python3 rpm_installer.py dossier` | Vérifier et installer n'importe quel dossier de RPM (avec son `SHA256SUMS`) |
| `sudo python3 deploy_bundle.py bundle.tar.gz` | Déployer le bundle sans lancer l'installation |

## Configuration

`config.json`, lu par `main.py` :

| Clé | Rôle |
|---|---|
| `libreoffice_rpm_dir` | Dossier des RPM de LibreOffice |
| `rpm_dir` | Dossier des autres RPM |
| `java_src_dir`, `java_version` | Dossier source du JDK et nom de sa version |
| `desktop_src_dir` | Dossier des fichiers `.desktop` |
| `gnome_extensions` | UUID des extensions GNOME à activer |
| `opt_app_dirs` | Dossiers sous `/opt/` à passer en 755 récursif |

Aucun mot de passe n'est stocké dans un fichier : les comptes se créent uniquement par saisie interactive.

## Arborescence

```
install.py             point d'entrée : déploie le bundle puis lance main.py
deploy_bundle.py       extrait l'archive et place les 4 dossiers sous /opt/install
main.py                orchestrateur (phases provision / accounts)
config.py, config.json lecture de la configuration
rpm_installer.py       vérification SHA256 et installation des RPM via dnf
libreoffice_setup.py   installation de LibreOffice + contrôle final
java_setup.py          déploiement du JDK, JAVA_HOME / PATH
password_policy.py     assouplissement de pwquality.conf
accounts.py            création de comptes locaux
shortcuts.py           copie des .desktop et droits
gnome_extensions.py    extensions GNOME via dconf
opt_permissions.py     chmod 755 récursif sous /opt
```

## Prérequis

- Cible : Oracle Linux 9.6 installé depuis l'ISO officielle, Python 3 (celui d'OL9.6 suffit), exécution en root.
- Construction du bundle : une VM OL9.6 **non mise à jour** avec accès internet, détails dans [INSTALL.md](INSTALL.md).
