"""Module 3 + 5 : copie des raccourcis .desktop pour tous les users et droits de lecture.

- Copie vers /usr/share/applications/ (tous users).
- chmod 644 pour que tout le monde puisse lire (et le bureau lancer) le raccourci.
"""

import glob    # Pour développer le motif *.desktop en liste de fichiers.
import os      # Pour assembler les chemins et poser les permissions.
import shutil  # Pour copier les fichiers.


def find_desktop_files(src_dir):
    if not os.path.isdir(src_dir):
        raise FileNotFoundError("Le dossier n'existe pas: " + src_dir)
    motif = os.path.join(src_dir, "*.desktop")

    fichiers = glob.glob(motif)
    if not fichiers:
        raise FileNotFoundError("Le dossier est vide: " + src_dir)

    return fichiers


def copy_desktop_files(src_dir, dest_dir="/usr/share/applications/"):
    fichiers = find_desktop_files(src_dir)

    copies = []
    for chemin in fichiers:
        nom = os.path.basename(chemin)
        destination = os.path.join(dest_dir, nom)

        # copy() (pas copy2) : on ne veut pas hériter des permissions/dates du fichier
        # source, seulement du contenu. Les permissions, on les pose nous-mêmes juste après.
        shutil.copy(chemin, destination)
        os.chmod(destination, 0o644)  # rw-r--r-- : tous les users peuvent lire le raccourci.

        copies.append(destination)

    return copies


if __name__ == "__main__":
    resultat = copy_desktop_files("C:/testdesktop", dest_dir="C:/testdesktop_dest")
    print(resultat)
