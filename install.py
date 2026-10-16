"""Single entry point: deploys the bundle then runs the full installation.
Point d'entrée unique : déploie le bundle puis lance l'installation complète.

Chains deploy_bundle.py (extraction + placing files) and main.py
Enchaîne deploy_bundle.py (extraction + placement des fichiers) et main.py
(RPM, Java, accounts, shortcuts, GNOME, /opt) in a single run.
(RPM, Java, comptes, shortcuts, GNOME, /opt) en un seul run.

--phase lets the two halves run separately (used by the ISO respin's firstboot
--phase permet de lancer les deux moitiés séparément (utilisé par le firstboot
flow, where account creation must stay interactive on the console while the
de l'ISO respin, où la création de comptes doit rester interactive sur la
rest runs unattended). Default "all" is the original one-shot behavior.
console alors que le reste tourne en non-interactif). "all" par défaut = comportement d'origine.

Usage: sudo python3 install.py /chemin/vers/bundle_install.tar.gz [--phase all|provision|accounts]
Usage : sudo python3 install.py /chemin/vers/bundle_install.tar.gz [--phase all|provision|accounts]
"""

import argparse

from deploy_bundle import deploy_bundle
from main import main as run_install


def install(archive_path, phase="all"):
    # The accounts-only phase needs nothing from the bundle (no RPM/Java/desktop
    # files involved), so skip re-deploying it when it already ran during "provision".
    if phase in ("all", "provision"):
        deploy_bundle(archive_path)
    run_install(phase)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_path")
    parser.add_argument("--phase", choices=["all", "provision", "accounts"], default="all")
    args = parser.parse_args()

    install(args.bundle_path, args.phase)
