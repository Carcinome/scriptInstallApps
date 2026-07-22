"""Orchestrator: custom OL9.6 workstation installer.
Orchestrateur : installeur de poste OL9.6 custom.

Execution order:
Ordre d'exécution :
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

import os

import rpm_installer
import java_setup
import password_policy
import accounts
import shortcuts
import gnome_extensions
import opt_permissions
from config import load_config


def run_provisioning(cfg):
    rpm_files = rpm_installer.verify_checksums(cfg["rpm_dir"])
    rpm_installer.install_rpms(rpm_files)

    java_setup.install_java(cfg["java_src_dir"], cfg["java_version"])

    # OL96_HARDENING_PROFILE : positionnee par le firstboot de l'ISO respin
    # quand un profil CIS/STIG a ete choisi (spoke Anaconda "Security Policy").
    # Absente (usage manuel historique) ou "none" -> comportement inchange.
    # Un profil actif signifie qu'OpenSCAP a deja durci pwquality.conf ; on
    # n'ecrase pas ce reglage avec l'assouplissement habituel.
    hardening_profile = os.environ.get("OL96_HARDENING_PROFILE", "none")
    if hardening_profile in ("", "none"):
        password_policy.relax_password_policy()
    else:
        print(
            f"Profil de durcissement '{hardening_profile}' actif : "
            "pwquality.conf laissé tel que remédié par OpenSCAP."
        )

    shortcuts.copy_desktop_files(cfg["desktop_src_dir"])

    gnome_extensions.enable_extensions(cfg["gnome_extensions"])

    for app_dir in cfg["opt_app_dirs"]:
        opt_permissions.set_opt_permissions(app_dir)


def run_accounts():
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


def main(phase="all"):
    cfg = load_config()

    if phase in ("all", "provision"):
        run_provisioning(cfg)

    if phase in ("all", "accounts"):
        run_accounts()


if __name__ == "__main__":
    main()
