"""Module 3 + 5: copying .desktop shortcuts for all users, and read permissions.
Module 3 + 5 : copie des raccourcis .desktop pour tous les users et droits de lecture.

- Copy to /usr/share/applications/ (all users).
- Copie vers /usr/share/applications/ (tous users).
- chmod 644 so everyone can read (and the desktop can launch) the shortcut.
- chmod 644 pour que tout le monde puisse lire (et le bureau lancer) le raccourci.
"""

import glob
# For expanding the *.desktop pattern into a list of files.
# Pour développer le motif *.desktop en liste de fichiers.
import os
# For joining paths and setting permissions.
# Pour assembler les chemins et poser les permissions.
import shutil
# For copying files.
# Pour copier les fichiers.


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

        # copy() (not copy2): we don't want to inherit the source file's
        # copy() (pas copy2) : on ne veut pas hériter des permissions/dates du fichier
        # permissions/dates, only its content. We set the permissions ourselves right after.
        # source, seulement du contenu. Les permissions, on les pose nous-mêmes juste après.
        shutil.copy(chemin, destination)
        # rw-r--r--: every user can read the shortcut.
        # rw-r--r-- : tous les users peuvent lire le raccourci.
        os.chmod(destination, 0o644)

        copies.append(destination)

    return copies


if __name__ == "__main__":
    resultat = copy_desktop_files("C:/testdesktop", dest_dir="C:/testdesktop_dest")
    print(resultat)
