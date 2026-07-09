"""Module 2: creating local accounts (useradd equivalent), groups, home directory.
Module 2 : création de comptes locaux (équivalent useradd), groupes, home directory.

We build this module step by step, function by function.
On construit ce module pas à pas, fonction par fonction.
"""

import os
import getpass
# Like input(), but doesn't display anything on screen: useful for a password.
# Comme input(), mais n'affiche rien à l'écran : utile pour un mot de passe.
import subprocess
# For launching useradd/chpasswd/chage the same way we would from the command line.
# Pour lancer useradd/chpasswd/chage comme en ligne de commande.


def prompt_user_info():
    # We keep asking as long as the username is empty: it's the only field we can't
    # On redemande tant que le username est vide : c'est le seul champ qu'on ne peut pas
    # leave at a default, useradd couldn't do anything without it.
    # laisser par défaut, useradd ne pourrait rien faire sans lui.
    username = input("Nom d'utilisateur : ").strip()
    while not username:
        username = input("Nom d'utilisateur (obligatoire) : ").strip()

    # getpass hides the input in the terminal, unlike input().
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

    # useradd with no option = all the system defaults (home in /home/<username>,
    # useradd sans option = tous les défauts du système (home dans /home/<username>,
    # default shell, no secondary group). That's what we want for now.
    # shell par défaut, pas de groupe secondaire). C'est ce qu'on veut pour l'instant.
    resultat = subprocess.run(["useradd", username], capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(
            f"Échec de useradd pour {username} (code {resultat.returncode}):\n{resultat.stderr}"
        )

    # chpasswd reads "username:password" on its standard input: the password
    # chpasswd lit "username:password" sur son entrée standard : le mot de passe
    # never appears as a command argument (so it's not visible in `ps aux`).
    # n'apparaît jamais comme argument de commande (donc pas visible dans `ps aux`).
    resultat = subprocess.run(
        ["chpasswd"], input=f"{username}:{password}\n", capture_output=True, text=True
    )
    if resultat.returncode != 0:
        raise RuntimeError(
            f"Échec de chpasswd pour {username} (code {resultat.returncode}):\n{resultat.stderr}"
        )

    if force_change:
        # chage -d 0 sets the last password change date to the epoch:
        # chage -d 0 met la date du dernier changement de mdp à l'epoch :
        # the system considers it expired, so it asks for a new one at the next login.
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
