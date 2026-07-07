"""Module Java : déploiement d'un JDK fourni en tarball (ex. Temurin) dans /opt/java/,
en remplacement du java par défaut, avec JAVA_HOME/PATH posés globalement.

Reprend le process manuel qui marchait déjà :
  sudo mkdir -p /opt/java
  sudo cp -r /opt/offline_bundle/java/<version> /opt/java/
  sudo chmod -R 755 /opt/java
  -> /etc/profile.d/java.sh avec JAVA_HOME + PATH, chmod 644
"""

import os
import shutil

import opt_permissions  # Réutilisé pour le chmod -R 755, déjà écrit au module 6.


def copy_java(java_src_dir, version_dirname, install_root="/opt/java"):
    src = os.path.join(java_src_dir, version_dirname)
    if not os.path.isdir(src):
        raise FileNotFoundError("Le dossier Java n'existe pas: " + src)

    os.makedirs(install_root, exist_ok=True)
    dest = os.path.join(install_root, version_dirname)

    # dirs_exist_ok=True : relance possible du script sans planter si /opt/java/<version> existe déjà.
    shutil.copytree(src, dest, dirs_exist_ok=True)

    return dest


def configure_java_env(java_home, profile_path="/etc/profile.d/java.sh"):
    contenu = f"export JAVA_HOME={java_home}\nexport PATH=$JAVA_HOME/bin:$PATH\n"

    with open(profile_path, "w") as f:
        f.write(contenu)
    os.chmod(profile_path, 0o644)

    # Pas besoin de "source" ici : /etc/profile.d/*.sh est de toute façon rechargé
    # automatiquement à chaque nouvelle connexion. Un "source" dans ce script n'aurait
    # d'effet que sur le process Python lui-même, pas sur les sessions des users.


def install_java(java_src_dir, version_dirname, install_root="/opt/java"):
    if os.geteuid() != 0:
        raise PermissionError("Installation de Java: il faut être root (sudo).")

    java_home = copy_java(java_src_dir, version_dirname, install_root)
    opt_permissions.set_opt_permissions(java_home)
    configure_java_env(java_home)


if __name__ == "__main__":
    install_java("/opt/offline_bundle/java", "8.0.392-tem")
