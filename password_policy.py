"""Relaxes the password complexity rules (/etc/security/pwquality.conf).
Assouplit les règles de complexité de mot de passe (/etc/security/pwquality.conf).

minlen = 5, everything else at 0 (maximum flexibility), usercheck = 0 to allow
minlen = 5, tout le reste à 0 (souplesse max), usercheck = 0 pour autoriser
the username as password. Applies when a user changes their own
le username comme mot de passe. S'applique quand un user change son propre
password via passwd (so mostly useful together with the accounts module's "force_change").
mot de passe via passwd (donc surtout utile avec le "force_change" du module comptes).
"""

import os
import re

REGLAGES = {
    "minlen": 5,
    "difok": 0,
    "dcredit": 0,
    "ucredit": 0,
    "lcredit": 0,
    "ocredit": 0,
    "minclass": 0,
    "maxrepeat": 0,
    "maxclassrepeat": 0,
    "maxsequence": 0,
    "usercheck": 0,
}


def relax_password_policy(conf_path="/etc/security/pwquality.conf", reglages=None):
    if os.geteuid() != 0:
        raise PermissionError("Modification de pwquality.conf: il faut être root (sudo).")

    if not os.path.isfile(conf_path):
        raise FileNotFoundError("Fichier introuvable: " + conf_path)

    if reglages is None:
        reglages = REGLAGES

    with open(conf_path) as f:
        lignes = f.readlines()

    # Whatever is left in this dict at the end of the loop = the keys missing from the file,
    # Ce qui reste dans ce dict à la fin de la boucle = les clés absentes du fichier,
    # to be appended at the end.
    # à ajouter à la fin.
    restants = dict(reglages)

    for i, ligne in enumerate(lignes):
        # A pwquality.conf line looks like "minlen = 8" or "# minlen = 8" (commented
        # Une ligne pwquality.conf ressemble à "minlen = 8" ou "# minlen = 8" (commentée
        # out by default). We spot the key whether it's commented or active.
        # par défaut). On repère la clé peu importe si elle est commentée ou active.
        m = re.match(r"^\s*#?\s*(\w+)\s*=", ligne)
        if m and m.group(1) in restants:
            cle = m.group(1)
            lignes[i] = f"{cle} = {restants.pop(cle)}\n"

    for cle, valeur in restants.items():
        lignes.append(f"{cle} = {valeur}\n")

    with open(conf_path, "w") as f:
        f.writelines(lignes)


if __name__ == "__main__":
    relax_password_policy()
