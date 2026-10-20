"""Module 1: discovering and installing RPMs from a local folder.
Module 1 : découverte et installation des RPM depuis un dossier local."""

import glob
# For expanding the *.rpm pattern into a list of files.
# Pour développer le motif *.rpm en liste de fichiers.
import os
# For properly joining the path (folder + pattern).
# Pour assembler proprement le chemin (dossier + motif).
import hashlib
# Hashing toolbox, shipped with Python.
# Boîte à outils de hashing, livrée avec Python.
import subprocess
# For launching dnf the same way we would from the command line.
# Pour lancer dnf comme on le ferait en ligne de commande.
import sys
# To read the arguments typed after the script name (sys.argv).
# Pour lire les arguments tapés après le nom du script (sys.argv).


def find_rpms(rpm_dir):
    # os.path.join glues the folder and the pattern together: "/opt/install/rpms" + "*.rpm".
    # os.path.join colle le dossier et le motif : "/opt/install/rpms" + "*.rpm".
    # -> "/opt/install/rpms/*.rpm".
    # -> "/opt/install/rpms/*.rpm".
    if not os.path.isdir(rpm_dir):
        raise FileNotFoundError("Le dossier n'existe pas: " + rpm_dir)
    motif = os.path.join(rpm_dir, "*.rpm")

    # glob.glob reads the disk and returns the list of paths matching the pattern.
    # glob.glob lit le disque et renvoie la liste des chemins qui collent au motif.
    # -> ["/opt/install/rpms/zabbix-agent.rpm", "/opt/install/rpms/postgresql.rpm", ...]
    # -> ["/opt/install/rpms/zabbix-agent.rpm", "/opt/install/rpms/postgresql.rpm", ...]
    fichiers = glob.glob(motif)

    # Safety net: the folder exists, but it might be empty.
    # Garde-fou : le dossier existe, mais il est peut-être vide.
    if not fichiers:
        raise FileNotFoundError("Le dossier est vide:" + rpm_dir)

    # We return this list to whoever called the function.
    # On renvoie cette liste à celui qui a appelé la fonction.
    return fichiers


def calculate_sha256(file_path):
    # 'rb' = read binary, we read the raw bytes.
    # 'rb' = read binary, on lit les octets bruts.
    with open(file_path, "rb") as f:
        contenu = f.read()
    return hashlib.sha256(contenu).hexdigest()


def parse_sha256sums(sums_file):
    # A SHA256SUMS line looks like:
    # Une ligne de SHA256SUMS ressemble à :
    # "3f786850e387550fdab836ed7e6dc881de23001b  paquet1.rpm"
    # "3f786850e387550fdab836ed7e6dc881de23001b  paquet1.rpm"
    # We want to turn it into a dict: {"paquet1.rpm": "3f786850..."}
    # On veut en tirer un dict : {"paquet1.rpm": "3f786850..."}
    empreintes = {}
    with open(sums_file) as f:
        for ligne in f:
            # Strips the \n and the surrounding whitespace.
            # Vire le \n et les espaces de bord.
            ligne = ligne.strip()
            if not ligne:
                # Skip blank lines.
                # On saute les lignes vides.
                continue

            # split(None, 1) cuts on the first run of whitespace, whether there's
            # split(None, 1) coupe sur la 1re série d'espaces, peu importe
            # 1 or 2 of them (the "*binary" vs "text" format).
            # qu'il y en ait 1 ou 2 (format "*binaire" vs "texte").
            empreinte, nom_fichier = ligne.split(None, 1)
            # The "*" marks binary mode in sha256sum.
            # Le "*" marque un mode binaire chez sha256sum.
            nom_fichier = nom_fichier.lstrip("*")
            empreintes[nom_fichier] = empreinte

    return empreintes


def verify_checksums(rpm_dir, sums_file=None):
    # By default, the SHA256SUMS file lives next to the RPMs.
    # Par défaut, le fichier SHA256SUMS vit à côté des RPM.
    if sums_file is None:
        sums_file = os.path.join(rpm_dir, "SHA256SUMS")

    fichiers = find_rpms(rpm_dir)
    empreintes_attendues = parse_sha256sums(sums_file)

    invalides = []
    for chemin in fichiers:
        nom = os.path.basename(chemin)
        attendu = empreintes_attendues.get(nom)

        if attendu is None:
            invalides.append(f"{nom}: absent de {os.path.basename(sums_file)}")
            continue

        obtenu = calculate_sha256(chemin)
        if obtenu != attendu:
            invalides.append(f"{nom}: empreinte différente (attendu {attendu}, obtenu {obtenu})")

    # We raise a single error grouping every issue, rather than
    # On lève une seule erreur groupant tous les problèmes, plutôt que
    # stopping at the first suspicious file: more useful to fix everything in one go.
    # de s'arrêter au premier fichier suspect : plus utile pour corriger d'un coup.
    if invalides:
        raise ValueError("Vérification SHA256 échouée:\n- " + "\n- ".join(invalides))

    # Everything checks out: we return the list of RPMs ready to be installed.
    # Tout est bon : on renvoie la liste des RPM prêts à être installés.
    return fichiers


def filter_older_than_installed(rpm_files):
    # The "rpm" Python module ships with dnf on OL9: it reads RPM headers and the database
    # Le module Python "rpm" est livré avec dnf sur OL9 : il lit les en-têtes RPM et la base
    # of installed packages, and applies RPM's exact version-comparison rules.
    # des paquets installés, et applique les règles exactes de comparaison de versions RPM.
    try:
        import rpm
    except ImportError:
        # Without it we cannot compare: keep everything, dnf will still refuse an impossible transaction.
        # Sans lui on ne peut pas comparer : on garde tout, dnf refusera quand même une transaction impossible.
        print("Module Python 'rpm' absent : comparaison des versions ignorée.")
        return rpm_files, []

    ts = rpm.TransactionSet()
    # We only read headers, so we skip signature checks (they would need the GPG keys).
    # On ne fait que lire des en-têtes, donc on saute les signatures (il faudrait les clés GPG).
    ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES | rpm._RPMVSF_NODIGESTS)

    # Installed packages: {(name, arch): (epoch, version, release)}, keeping the highest version.
    # Paquets installés : {(nom, arch): (epoch, version, release)}, en gardant la plus haute version.
    installed = {}
    for header in ts.dbMatch():
        cle = (header[rpm.RPMTAG_NAME], header[rpm.RPMTAG_ARCH])
        evr = (
            str(header[rpm.RPMTAG_EPOCHNUM] or 0),
            header[rpm.RPMTAG_VERSION],
            header[rpm.RPMTAG_RELEASE],
        )
        if cle not in installed or rpm.labelCompare(evr, installed[cle]) > 0:
            installed[cle] = evr

    garder = []
    ignores = []
    for chemin in rpm_files:
        try:
            with open(chemin, "rb") as f:
                header = ts.hdrFromFdno(f.fileno())
        except rpm.error:
            # Unreadable header: when in doubt, let dnf decide.
            # En-tête illisible : dans le doute, on laisse dnf trancher.
            garder.append(chemin)
            continue

        cle = (header[rpm.RPMTAG_NAME], header[rpm.RPMTAG_ARCH])
        evr = (
            str(header[rpm.RPMTAG_EPOCHNUM] or 0),
            header[rpm.RPMTAG_VERSION],
            header[rpm.RPMTAG_RELEASE],
        )

        # Strictly older than what is installed: installing it would be a downgrade.
        # Strictement plus ancien que l'installé : l'installer reviendrait à rétrograder.
        # Equal or newer, or not installed at all: we keep it.
        # Identique, plus récent, ou pas installé du tout : on le garde.
        if cle in installed and rpm.labelCompare(evr, installed[cle]) < 0:
            ignores.append(
                f"{cle[0]}.{cle[1]} {evr[1]}-{evr[2]} "
                f"(installé : {installed[cle][1]}-{installed[cle][2]})"
            )
        else:
            garder.append(chemin)

    return garder, ignores


def install_rpms(rpm_files):
    if os.geteuid() != 0:
        raise PermissionError("Installation des RPM: il faut être root (sudo).")

    # Drop the files that would downgrade an already-installed package (typical on machines
    # On écarte les fichiers qui rétrograderaient un paquet déjà installé (cas typique des postes
    # deployed with an older bundle that came with newer packages than the OL9.6 ISO).
    # déployés avec un ancien bundle, dont les paquets sont plus récents que ceux de l'ISO OL9.6).
    rpm_files, ignores = filter_older_than_installed(rpm_files)
    for ligne in ignores:
        print("Ignoré, version plus récente déjà installée : " + ligne)

    if not rpm_files:
        # Everything was already there in an equal or newer version: nothing left for dnf to do.
        # Tout était déjà là en version identique ou plus récente : il ne reste rien à faire pour dnf.
        return ""

    # dnf knows how to resolve dependencies between several given local files
    # dnf sait résoudre les dépendances entre plusieurs fichiers locaux donnés
    # in a single transaction, unlike "rpm -Uvh" which requires a manual order.
    # en une seule transaction, contrairement à "rpm -Uvh" qui exige un ordre manuel.
    # --disablerepo=*: we forbid any call to remote repos, only the
    # --disablerepo=* : on interdit tout appel aux dépôts distants, seuls les
    # supplied files (and their dependencies already present in rpm_files) count.
    # fichiers fournis (et leurs dépendances déjà présentes dans rpm_files) comptent.
    commande = ["dnf", "install", "-y", "--disablerepo=*"] + rpm_files

    resultat = subprocess.run(commande, capture_output=True, text=True)

    if resultat.returncode != 0:
        raise RuntimeError(
            f"Échec de l'installation des RPM (code {resultat.returncode}):\n{resultat.stderr}"
        )

    return resultat.stdout


if __name__ == "__main__":
    # Standalone use: verify then install any folder of RPMs, e.g. the LibreOffice one.
    # Usage autonome : vérifier puis installer n'importe quel dossier de RPM, ex. celui de LibreOffice.
    # Usage: sudo python3 rpm_installer.py /opt/install/libreoffice
    # Usage : sudo python3 rpm_installer.py /opt/install/libreoffice
    if len(sys.argv) != 2:
        print("Usage: sudo python3 rpm_installer.py /chemin/vers/dossier_rpm")
        sys.exit(1)

    rpm_files = verify_checksums(sys.argv[1])
    install_rpms(rpm_files)
    print(f"Installation terminée depuis {sys.argv[1]}.")
