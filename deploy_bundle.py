"""Script à part : déploie une tar archive "all in one" vers les dossiers attendus par main.py.

Structure attendue dans l'archive (tarfile détecte tout seul compressé ou pas) :
  opt/install/rpms/*.rpm + SHA256SUMS
  opt/install/desktop/*.desktop
  opt/install/java/<version>/

Usage : sudo python3 deploy_bundle.py /chemin/vers/bundle_install.tar.gz
"""

import os
import shutil
import sys
import tarfile
import tempfile

# Sous-dossiers attendus dans l'archive, sous "opt/install/", et leur destination finale.
DESTINATIONS = {
    "rpms": "/opt/install/rpms",
    "desktop": "/opt/install/desktop",
    "java": "/opt/install/java",
}


def deploy_bundle(archive_path):
    if os.geteuid() != 0:
        raise PermissionError("Déploiement du bundle: il faut être root (sudo).")

    if not os.path.isfile(archive_path):
        raise FileNotFoundError("L'archive n'existe pas: " + archive_path)

    work_dir = tempfile.mkdtemp(prefix="bundle_")
    try:
        # "r:*" laisse tarfile deviner tout seul si c'est compressé (gz, bz2...) ou pas,
        # peu importe ce que dit l'extension du fichier.
        # Pas de paramètre "filter" ici : il n'existe qu'à partir de Python 3.12,
        # et OL9.6 tourne encore en python3.9 par défaut - ça planterait sinon.
        with tarfile.open(archive_path, "r:*") as archive:
            archive.extractall(work_dir)

        for nom_dossier, destination in DESTINATIONS.items():
            source = os.path.join(work_dir, "opt", "install", nom_dossier)
            if not os.path.isdir(source):
                raise FileNotFoundError(
                    f"L'archive ne contient pas 'opt/install/{nom_dossier}/'"
                )

            # On repart d'un dossier destination vide à chaque déploiement : ça évite
            # de mélanger un ancien bundle avec le nouveau (on s'est déjà fait avoir
            # une fois avec des RPM d'une vieille version qui traînaient).
            if os.path.isdir(destination):
                shutil.rmtree(destination)
            shutil.copytree(source, destination)

            print(f"opt/install/{nom_dossier}/ -> {destination}")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: sudo python3 deploy_bundle.py /chemin/vers/bundle_install.tar.gz")
        sys.exit(1)

    deploy_bundle(sys.argv[1])
