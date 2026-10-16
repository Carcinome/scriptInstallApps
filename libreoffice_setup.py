"""LibreOffice module: installing the LibreOffice suite from a local RPM folder.
Module LibreOffice : installation de la suite LibreOffice depuis un dossier local de RPM.

Can run on its own, outside install.py / main.py (like accounts.py):
Peut tourner seul, hors install.py / main.py (comme accounts.py) :
  sudo python3 libreoffice_setup.py [/chemin/vers/dossier_rpm]
"""

import subprocess
import sys

import rpm_installer
# Reused: the SHA256 check and the dnf install are exactly the same as for the other RPMs.
# Réutilisé : la vérif SHA256 et le dnf install sont exactement les mêmes que pour les autres RPM.

# Default folder where the bundle puts the LibreOffice RPMs.
# Dossier par défaut où le bundle dépose les RPM de LibreOffice.
DEFAULT_RPM_DIR = "/opt/install/libreoffice"

# Packages that must be present once the install is done.
# Paquets qui doivent être présents une fois l'installation terminée.
REQUIRED_PACKAGES = [
    "libreoffice-core",
    "libreoffice-writer",
    "libreoffice-calc",
    "libreoffice-impress",
]


def verify_libreoffice():
    # "rpm -q" asks the RPM database whether each package is installed.
    # "rpm -q" demande à la base RPM si chaque paquet est installé.
    # It returns a non-zero code as soon as one of them is missing.
    # Il renvoie un code non nul dès qu'un seul est absent.
    resultat = subprocess.run(
        ["rpm", "-q"] + REQUIRED_PACKAGES, capture_output=True, text=True
    )
    if resultat.returncode != 0:
        raise RuntimeError(
            "LibreOffice incomplet après installation:\n" + resultat.stdout + resultat.stderr
        )


def install_libreoffice(rpm_dir=DEFAULT_RPM_DIR):
    # Same chain as the other RPMs: check the hashes, then install.
    # Même enchaînement que pour les autres RPM : on vérifie les empreintes, puis on installe.
    rpm_files = rpm_installer.verify_checksums(rpm_dir)
    rpm_installer.install_rpms(rpm_files)

    # dnf can answer "ok" while something is still missing: we check ourselves.
    # dnf peut répondre "ok" alors qu'il manque quelque chose : on vérifie nous-mêmes.
    verify_libreoffice()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Usage: sudo python3 libreoffice_setup.py [/chemin/vers/dossier_rpm]")
        sys.exit(1)

    dossier = sys.argv[1] if len(sys.argv) == 2 else DEFAULT_RPM_DIR
    install_libreoffice(dossier)
    print("LibreOffice installé.")
