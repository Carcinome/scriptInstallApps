import glob     # Pour développer le motif *.rpm en liste de fichiers.
import os       # Pour assembler proprement le chemin (dossier + motif).
import hashlib  # Boîte à outils de hashing, livrée avec Python.


def find_rpms(rpm_dir):
    # os.path.join colle le dossier et le motif : "/opt/install/rpms" + "*.rpm".
    # -> "/opt/install/rpms/*.rpm".
    if not os.path.isdir(rpm_dir):
        raise FileNotFoundError ("Le dossier n'existe pas: "+ rpm_dir)
    motif = os.path.join(rpm_dir, "*.rpm")

    # glob.glob lit le disque et renvoie la liste des chemins qui collent au motif.
    # -> ["/opt/install/rpms/zabbix-agent.rpm", "/opt/install/rpms/postgresql.rpm", ...]
    fichiers = glob.glob(motif)

    # Garde-fou : le dossier existe, mais il est peut-être vide.
    if not fichiers:
        raise FileNotFoundError ("Le dossier est vide:" + rpm_dir)

    # On renvoie cette liste à celui qui a appelé la fonction.
    return fichiers

resultat = find_rpms("C:/testrpms")
print(resultat)


# On ouvre le fichier en mode binaire pour lire ses octets bruts. rb = 'read binary'.
with open("C:/testrpms/paquet1.rpm", "rb") as f: # With pour fermer le fichier automatiquement.
    contenu = f.read() # Aspire tout le contenu du fichier en octets.

# Calcul de l'empreinte en hexadécimal.
empreinte = hashlib.sha256(contenu).hexdigest() # Passe ces octets dans la moulinette sha256
# et .hexdigest() sort le résultat en texte hexadécimal lisible.
print(empreinte)


def calculate_sha256(file_path):
    with open(file_path, "rb") as f:
        contenu = f.read()
    return hashlib.sha256(contenu).hexdigest()
