"""Module 6 : chmod 755 récursif (dossiers ET fichiers) sur les dossiers d'applis dans /opt/."""

import os


def set_opt_permissions(app_dir):
    if not os.path.isdir(app_dir):
        raise FileNotFoundError("Le dossier n'existe pas: " + app_dir)

    if os.geteuid() != 0:
        raise PermissionError("chmod sur /opt: il faut être root (sudo).")

    os.chmod(app_dir, 0o755)  # Le dossier racine lui-même.

    for racine, dossiers, fichiers in os.walk(app_dir):
        for nom in dossiers:
            os.chmod(os.path.join(racine, nom), 0o755)
        for nom in fichiers:
            os.chmod(os.path.join(racine, nom), 0o755)


if __name__ == "__main__":
    set_opt_permissions("/opt/exemple")
