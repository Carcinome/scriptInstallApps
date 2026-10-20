"""Module 6: recursive chmod 755 (folders AND files) on the app folders under /opt/.
Module 6 : chmod 755 récursif (dossiers ET fichiers) sur les dossiers d'applis dans /opt/."""

import os


def set_opt_permissions(app_dir):
    if not os.path.isdir(app_dir):
        raise FileNotFoundError("Le dossier n'existe pas: " + app_dir)

    if os.geteuid() != 0:
        raise PermissionError("chmod sur /opt: il faut être root (sudo).")

    # The root folder itself.
    # Le dossier racine lui-même.
    os.chmod(app_dir, 0o755)

    for racine, dossiers, fichiers in os.walk(app_dir):
        for nom in dossiers + fichiers:
            chemin = os.path.join(racine, nom)
            # os.chmod follows symbolic links and would change the permissions of the target,
            # os.chmod suit les liens symboliques et changerait les droits de la cible,
            # which could be outside the app folder: we skip the links themselves.
            # qui pourrait être hors du dossier de l'appli : on saute les liens eux-mêmes.
            if os.path.islink(chemin):
                continue
            os.chmod(chemin, 0o755)


if __name__ == "__main__":
    set_opt_permissions("/opt/install")
