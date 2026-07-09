"""Single entry point: deploys the bundle then runs the full installation.
Point d'entrée unique : déploie le bundle puis lance l'installation complète.

Chains deploy_bundle.py (extraction + placing files) and main.py
Enchaîne deploy_bundle.py (extraction + placement des fichiers) et main.py
(RPM, Java, accounts, shortcuts, GNOME, /opt) in a single run.
(RPM, Java, comptes, shortcuts, GNOME, /opt) en un seul run.

Usage: sudo python3 install.py /chemin/vers/bundle_install.tar.gz
Usage : sudo python3 install.py /chemin/vers/bundle_install.tar.gz
"""

import sys

from deploy_bundle import deploy_bundle
from main import main as run_install


def install(archive_path):
    deploy_bundle(archive_path)
    run_install()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: sudo python3 install.py /chemin/vers/bundle_install.tar.gz")
        sys.exit(1)

    install(sys.argv[1])
