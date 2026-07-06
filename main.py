"""Orchestrateur : installeur de poste OL9.6 custom.

Ordre d'exécution :
1. Installation des RPM et dépendances (rpm_installer)
2. Création des comptes locaux (accounts) - interactif, pas piloté par la config
3. Copie des raccourcis menu démarrer (shortcuts)
4. Activation des extensions GNOME (gnome_extensions)
5. Droits sur les raccourcis (shortcuts, fait en même temps que la copie)
6. chmod 755 sur /opt (opt_permissions)
"""

import rpm_installer
import accounts
import shortcuts
import gnome_extensions
import opt_permissions
from config import load_config


def main():
    cfg = load_config()

    rpm_files = rpm_installer.verify_checksums(cfg["rpm_dir"])
    rpm_installer.install_rpms(rpm_files)

    shortcuts.copy_desktop_files(cfg["desktop_src_dir"])

    gnome_extensions.enable_extensions(cfg["gnome_extensions"])

    for app_dir in cfg["opt_app_dirs"]:
        opt_permissions.set_opt_permissions(app_dir)

    # Comptes : pas dans la config (pas de mot de passe en clair dans un fichier),
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
