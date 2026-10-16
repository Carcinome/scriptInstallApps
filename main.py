"""Orchestrator: custom OL9.6 workstation installer.
Orchestrateur : installeur de poste OL9.6 custom.

Execution order:
Ordre d'exécution :
0. Installing LibreOffice and its full dependency set, first, so it matches the base OS (rpm_installer)
0. Installation de LibreOffice et de tout son jeu de dépendances, en premier, pour coller à l'OS de base (rpm_installer)
1. Installing RPMs and dependencies (rpm_installer)
1. Installation des RPM et dépendances (rpm_installer)
1bis. Deploying the JDK tarball, replaces the default java (java_setup)
1bis. Déploiement du JDK en tarball, remplace le java par défaut (java_setup)
2. Relaxing the password policy (password_policy)
2. Assouplissement de la politique de mot de passe (password_policy)
2bis. Creating local accounts (accounts) - interactive, not config-driven
2bis. Création des comptes locaux (accounts) - interactif, pas piloté par la config
3. Copying start menu shortcuts (shortcuts)
3. Copie des raccourcis menu démarrer (shortcuts)
4. Enabling GNOME extensions (gnome_extensions)
4. Activation des extensions GNOME (gnome_extensions)
5. Permissions on the shortcuts (shortcuts, done at the same time as the copy)
5. Droits sur les raccourcis (shortcuts, fait en même temps que la copie)
6. chmod 755 on /opt (opt_permissions)
6. chmod 755 sur /opt (opt_permissions)
"""

import rpm_installer
import libreoffice_setup
import java_setup
import password_policy
import accounts
import shortcuts
import gnome_extensions
import opt_permissions
from config import load_config


def main():
    cfg = load_config()

    # LibreOffice goes first, in its own dnf transaction: its RPMs were downloaded
    # LibreOffice passe en premier, dans sa propre transaction dnf : ses RPM ont été téléchargés
    # from the OL9.6 install ISO, so they match the virgin OS exactly.
    # depuis l'ISO d'installation OL9.6, donc ils collent exactement à l'OS vierge.
    libreoffice_setup.install_libreoffice(cfg["libreoffice_rpm_dir"])

    rpm_files = rpm_installer.verify_checksums(cfg["rpm_dir"])
    rpm_installer.install_rpms(rpm_files)

    java_setup.install_java(cfg["java_src_dir"], cfg["java_version"])

    password_policy.relax_password_policy()

    shortcuts.copy_desktop_files(cfg["desktop_src_dir"])

    gnome_extensions.enable_extensions(cfg["gnome_extensions"])

    for app_dir in cfg["opt_app_dirs"]:
        opt_permissions.set_opt_permissions(app_dir)

    # Accounts: not in the config (no plaintext password in a file),
    # Comptes : pas dans la config (pas de mot de passe en clair dans un fichier),
    # we loop on the interactive prompt as long as we want to create one more account.
    # on boucle sur le prompt interactif tant qu'on veut créer un compte de plus.
    while True:
        reponse = input("Créer un compte utilisateur ? (o/N) : ").strip().lower()
        if reponse != "o":
            break
        infos = accounts.prompt_user_info()
        accounts.create_user(**infos)
        print(f"Compte {infos['username']!r} créé.")


if __name__ == "__main__":
    main()
