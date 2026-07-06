"""Module 1 : découverte et installation des RPM depuis un dossier local."""

import glob        # Pour développer le motif *.rpm en liste de fichiers.
import os          # Pour assembler proprement le chemin (dossier + motif).
import hashlib     # Boîte à outils de hashing, livrée avec Python.
import subprocess  # Pour lancer dnf comme on le ferait en ligne de commande.


def find_rpms(rpm_dir):
    # os.path.join colle le dossier et le motif : "/opt/install/rpms" + "*.rpm".
    # -> "/opt/install/rpms/*.rpm".
    if not os.path.isdir(rpm_dir):
        raise FileNotFoundError("Le dossier n'existe pas: " + rpm_dir)
    motif = os.path.join(rpm_dir, "*.rpm")

    # glob.glob lit le disque et renvoie la liste des chemins qui collent au motif.
    # -> ["/opt/install/rpms/zabbix-agent.rpm", "/opt/install/rpms/postgresql.rpm", ...]
    fichiers = glob.glob(motif)

    # Garde-fou : le dossier existe, mais il est peut-être vide.
    if not fichiers:
        raise FileNotFoundError("Le dossier est vide:" + rpm_dir)

    # On renvoie cette liste à celui qui a appelé la fonction.
    return fichiers


def calculate_sha256(file_path):
    with open(file_path, "rb") as f:  # 'rb' = read binary, on lit les octets bruts.
        contenu = f.read()
    return hashlib.sha256(contenu).hexdigest()


def parse_sha256sums(sums_file):
    # Une ligne de SHA256SUMS ressemble à :
    # "3f786850e387550fdab836ed7e6dc881de23001b  paquet1.rpm"
    # On veut en tirer un dict : {"paquet1.rpm": "3f786850..."}
    empreintes = {}
    with open(sums_file) as f:
        for ligne in f:
            ligne = ligne.strip()  # Vire le \n et les espaces de bord.
            if not ligne:
                continue  # On saute les lignes vides.

            # split(None, 1) coupe sur la 1re série d'espaces, peu importe
            # qu'il y en ait 1 ou 2 (format "*binaire" vs "texte").
            empreinte, nom_fichier = ligne.split(None, 1)
            nom_fichier = nom_fichier.lstrip("*")  # Le "*" marque un mode binaire chez sha256sum.
            empreintes[nom_fichier] = empreinte

    return empreintes


def verify_checksums(rpm_dir, sums_file=None):
    # Par défaut, le fichier SHA256SUMS vit à côté des RPM.
    if sums_file is None:
        sums_file = os.path.join(rpm_dir, "SHA256SUMS")

    fichiers = find_rpms(rpm_dir)
    empreintes_attendues = parse_sha256sums(sums_file)

    invalides = []
    for chemin in fichiers:
        nom = os.path.basename(chemin)
        attendu = empreintes_attendues.get(nom)

        if attendu is None:
            invalides.append(f"{nom}: absent de {os.path.basename(sums_file)}")
            continue

        obtenu = calculate_sha256(chemin)
        if obtenu != attendu:
            invalides.append(f"{nom}: empreinte différente (attendu {attendu}, obtenu {obtenu})")

    # On lève une seule erreur groupant tous les problèmes, plutôt que
    # de s'arrêter au premier fichier suspect : plus utile pour corriger d'un coup.
    if invalides:
        raise ValueError("Vérification SHA256 échouée:\n- " + "\n- ".join(invalides))

    # Tout est bon : on renvoie la liste des RPM prêts à être installés.
    return fichiers


def install_rpms(rpm_files):
    if os.geteuid() != 0:
        raise PermissionError("Installation des RPM: il faut être root (sudo).")

    # dnf sait résoudre les dépendances entre plusieurs fichiers locaux donnés
    # en une seule transaction, contrairement à "rpm -Uvh" qui exige un ordre manuel.
    # --disablerepo=* : on interdit tout appel aux dépôts distants, seuls les
    # fichiers fournis (et leurs dépendances déjà présentes dans rpm_files) comptent.
    commande = ["dnf", "install", "-y", "--disablerepo=*"] + rpm_files

    resultat = subprocess.run(commande, capture_output=True, text=True)

    if resultat.returncode != 0:
        raise RuntimeError(
            f"Échec de l'installation des RPM (code {resultat.returncode}):\n{resultat.stderr}"
        )

    return resultat.stdout


if __name__ == "__main__":
    resultat = find_rpms("C:/testrpms")
    print(resultat)

    print(calculate_sha256("C:/testrpms/paquet1.rpm"))

    with open("C:/testrpms/SHA256SUMS") as f:
        for ligne in f:
            print(repr(ligne))
