"""Java module: deploying a JDK shipped as a tarball (e.g. Temurin) into /opt/java/,
Module Java : déploiement d'un JDK fourni en tarball (ex. Temurin) dans /opt/java/,
replacing the default java, with JAVA_HOME/PATH set globally.
en remplacement du java par défaut, avec JAVA_HOME/PATH posés globalement.

Reproduces the manual process that already worked:
Reprend le process manuel qui marchait déjà :
  sudo mkdir -p /opt/java
  sudo cp -r /opt/offline_bundle/java/<version> /opt/java/
  sudo chmod -R 755 /opt/java
  -> /etc/profile.d/java.sh avec JAVA_HOME + PATH, chmod 644
"""

import os
import shutil

import opt_permissions
# Reused for the chmod -R 755, already written in module 6.
# Réutilisé pour le chmod -R 755, déjà écrit au module 6.


def copy_java(java_src_dir, version_dirname, install_root="/opt/java"):
    src = os.path.join(java_src_dir, version_dirname)
    if not os.path.isdir(src):
        raise FileNotFoundError("Le dossier Java n'existe pas: " + src)

    os.makedirs(install_root, exist_ok=True)
    dest = os.path.join(install_root, version_dirname)

    # dirs_exist_ok=True: lets the script be rerun without crashing if /opt/java/<version> already exists.
    # dirs_exist_ok=True : relance possible du script sans planter si /opt/java/<version> existe déjà.
    shutil.copytree(src, dest, dirs_exist_ok=True)

    return dest


def configure_java_env(java_home, profile_path="/etc/profile.d/java.sh"):
    contenu = f"export JAVA_HOME={java_home}\nexport PATH=$JAVA_HOME/bin:$PATH\n"

    with open(profile_path, "w") as f:
        f.write(contenu)
    os.chmod(profile_path, 0o644)

    # No need to "source" it here: /etc/profile.d/*.sh is reloaded
    # Pas besoin de "source" ici : /etc/profile.d/*.sh est de toute façon rechargé
    # automatically at every new login anyway. A "source" in this script would only
    # automatiquement à chaque nouvelle connexion. Un "source" dans ce script n'aurait
    # affect the Python process itself, not the users' sessions.
    # d'effet que sur le process Python lui-même, pas sur les sessions des users.


def install_java(java_src_dir, version_dirname, install_root="/opt/java"):
    if os.geteuid() != 0:
        raise PermissionError("Installation de Java: il faut être root (sudo).")

    java_home = copy_java(java_src_dir, version_dirname, install_root)
    opt_permissions.set_opt_permissions(java_home)
    configure_java_env(java_home)


if __name__ == "__main__":
    install_java("/opt/offline_bundle/java", "8.0.392-tem")
