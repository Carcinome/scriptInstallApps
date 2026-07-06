"""Module 4 : activation d'extensions GNOME via dconf, en réglage par défaut système.

Pourquoi dconf plutôt que "gnome-extensions enable" ou "gsettings set" tout court :
ces deux commandes parlent au processus GNOME Shell / D-Bus de l'utilisateur en cours,
donc il faut une session graphique déjà ouverte pour cet utilisateur précis. Juste après
un `useradd`, personne ne s'est encore connecté : il n'y a pas de session. En écrivant
directement dans la base dconf système (/etc/dconf/db/local.d/), on pose une valeur par
défaut qui s'applique à tous les users dès leur toute première connexion, sans session
préalable.
"""

import os
import subprocess  # Pour lancer "dconf update" comme en ligne de commande.


def ensure_dconf_profile(profile_path="/etc/dconf/profile/user"):
    # Le profil "user" dit à dconf où chercher les valeurs par défaut système
    # (system-db:local -> /etc/dconf/db/local.d/*). Sans cette ligne, nos réglages
    # dans local.d sont ignorés.
    contenu_attendu = "user-db:user\nsystem-db:local\n"

    if os.path.exists(profile_path):
        with open(profile_path) as f:
            contenu = f.read()
        if "system-db:local" in contenu:
            return  # Déjà en place, rien à faire.

    os.makedirs(os.path.dirname(profile_path), exist_ok=True)
    with open(profile_path, "w") as f:
        f.write(contenu_attendu)


def write_extensions_profile(extension_uuids, db_dir="/etc/dconf/db/local.d"):
    os.makedirs(db_dir, exist_ok=True)

    # dconf attend une liste au format GVariant : ['uuid1', 'uuid2'].
    liste = ", ".join(f"'{uuid}'" for uuid in extension_uuids)
    contenu = f"[org/gnome/shell]\nenabled-extensions=[{liste}]\n"

    chemin = os.path.join(db_dir, "00-extensions")
    with open(chemin, "w") as f:
        f.write(contenu)

    return chemin


def apply_dconf():
    # dconf update compile les fichiers texte de db/local.d/ en base binaire :
    # sans ça, nos changements ne sont jamais pris en compte.
    resultat = subprocess.run(["dconf", "update"], capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(f"Échec de dconf update (code {resultat.returncode}):\n{resultat.stderr}")


def enable_extensions(extension_uuids):
    if os.geteuid() != 0:
        raise PermissionError("Activation des extensions GNOME: il faut être root (sudo).")

    ensure_dconf_profile()
    write_extensions_profile(extension_uuids)
    apply_dconf()


if __name__ == "__main__":
    enable_extensions(["exemple@exemple.com"])
