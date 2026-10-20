"""Standalone script: deploys an "all in one" tar archive to the folders expected by main.py.
Script à part : déploie une tar archive "all in one" vers les dossiers attendus par main.py.

Expected structure inside the archive (tarfile auto-detects compressed or not):
Structure attendue dans l'archive (tarfile détecte tout seul compressé ou pas) :
  opt/install/libreoffice/*.rpm + SHA256SUMS
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
    "libreoffice": "/opt/install/libreoffice",
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
        # The "data" filter refuses absolute paths, ".." paths and links pointing outside the
        # Le filtre "data" refuse les chemins absolus, les chemins ".." et les liens qui sortent du
        # destination folder (CVE-2007-4559). Python 3.9 on OL9 has it (backported), but older
        # dossier de destination (CVE-2007-4559). Le Python 3.9 d'OL9 l'a (rétroporté), mais des
        # builds don't: hasattr() checks, so we never pass a parameter Python doesn't know.
        # versions plus anciennes non : hasattr() vérifie, on ne passe jamais un paramètre inconnu.
        with tarfile.open(archive_path, "r:*") as archive:
            if hasattr(tarfile, "data_filter"):
                archive.extractall(work_dir, filter="data")
            else:
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
            # symlinks=True recreates symbolic links as links (the JDK has two), instead of
            # symlinks=True recrée les liens symboliques comme des liens (le JDK en a deux), au lieu
            # copying the content they point to.
            # de copier le contenu pointé.
            shutil.copytree(source, destination, symlinks=True)

            print(f"opt/install/{nom_dossier}/ -> {destination}")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: sudo python3 deploy_bundle.py /chemin/vers/bundle_install.tar.gz")
        sys.exit(1)

    deploy_bundle(sys.argv[1])
