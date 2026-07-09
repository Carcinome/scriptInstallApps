"""Standalone script: deploys an "all in one" tar archive to the folders expected by main.py.
Script à part : déploie une tar archive "all in one" vers les dossiers attendus par main.py.

Expected structure inside the archive (tarfile auto-detects compressed or not):
Structure attendue dans l'archive (tarfile détecte tout seul compressé ou pas) :
  opt/install/rpms/*.rpm + SHA256SUMS
  opt/install/desktop/*.desktop
  opt/install/java/<version>/

Usage: sudo python3 deploy_bundle.py /chemin/vers/bundle_install.tar.gz
Usage : sudo python3 deploy_bundle.py /chemin/vers/bundle_install.tar.gz
"""

import os
import shutil
import sys
import tarfile
import tempfile

# Subfolders expected inside the archive, under "opt/install/", and their final destination.
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
        # "r:*" lets tarfile figure out on its own whether it's compressed (gz, bz2...) or not,
        # "r:*" laisse tarfile deviner tout seul si c'est compressé (gz, bz2...) ou pas,
        # regardless of what the file extension claims.
        # peu importe ce que dit l'extension du fichier.
        # No "filter" parameter here: it only exists from Python 3.12 onward,
        # Pas de paramètre "filter" ici : il n'existe qu'à partir de Python 3.12,
        # and OL9.6 still runs python3.9 by default - it would crash otherwise.
        # et OL9.6 tourne encore en python3.9 par défaut - ça planterait sinon.
        with tarfile.open(archive_path, "r:*") as archive:
            archive.extractall(work_dir)

        for nom_dossier, destination in DESTINATIONS.items():
            source = os.path.join(work_dir, "opt", "install", nom_dossier)
            if not os.path.isdir(source):
                raise FileNotFoundError(
                    f"L'archive ne contient pas 'opt/install/{nom_dossier}/'"
                )

            # We start from an empty destination folder on every deployment: this avoids
            # On repart d'un dossier destination vide à chaque déploiement : ça évite
            # mixing an old bundle with the new one (we already got burned once
            # de mélanger un ancien bundle avec le nouveau (on s'est déjà fait avoir
            # with RPMs from an old version lying around).
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
