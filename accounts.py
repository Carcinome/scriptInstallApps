"""Module 2 : création de comptes locaux (équivalent useradd), groupes, home directory.

On construit ce module pas à pas, fonction par fonction.
"""

import os
import getpass     # Comme input(), mais n'affiche rien à l'écran : utile pour un mot de passe.
import subprocess  # Pour lancer useradd/chpasswd/chage comme en ligne de commande.


def prompt_user_info():
    # On redemande tant que le username est vide : c'est le seul champ qu'on ne peut pas
    # laisser par défaut, useradd ne pourrait rien faire sans lui.
    username = input("Nom d'utilisateur : ").strip()
    while not username:
        username = input("Nom d'utilisateur (obligatoire) : ").strip()

    # getpass masque la saisie dans le terminal, contrairement à input().
    password = getpass.getpass("Mot de passe temporaire : ")

    reponse = input(
        "Forcer le changement de mot de passe à la prochaine connexion ? "
        "(1 = oui, Entrée = non) : "
    ).strip()
    force_change = reponse == "1"

    return {
        "username": username,
        "password": password,
        "force_change": force_change,
    }


def create_user(username, password, force_change=False):
    if os.geteuid() != 0:
        raise PermissionError("Création de compte: il faut être root (sudo).")

    # useradd sans option = tous les défauts du système (home dans /home/<username>,
    # shell par défaut, pas de groupe secondaire). C'est ce qu'on veut pour l'instant.
    resultat = subprocess.run(["useradd", username], capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(
            f"Échec de useradd pour {username} (code {resultat.returncode}):\n{resultat.stderr}"
        )

    # chpasswd lit "username:password" sur son entrée standard : le mot de passe
    # n'apparaît jamais comme argument de commande (donc pas visible dans `ps aux`).
    resultat = subprocess.run(
        ["chpasswd"], input=f"{username}:{password}\n", capture_output=True, text=True
    )
    if resultat.returncode != 0:
        raise RuntimeError(
            f"Échec de chpasswd pour {username} (code {resultat.returncode}):\n{resultat.stderr}"
        )

    if force_change:
        # chage -d 0 met la date du dernier changement de mdp à l'epoch :
        # le système considère qu'il a expiré, donc il en redemande un neuf au prochain login.
        resultat = subprocess.run(["chage", "-d", "0", username], capture_output=True, text=True)
        if resultat.returncode != 0:
            raise RuntimeError(
                f"Échec de chage pour {username} (code {resultat.returncode}):\n{resultat.stderr}"
            )


if __name__ == "__main__":
    infos = prompt_user_info()
    create_user(**infos)
    print(f"Compte {infos['username']!r} créé.")
