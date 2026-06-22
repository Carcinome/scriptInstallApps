import glob # Pour développer le motif *.rpm en liste de fichiers.
import os   # Pour assembler proprement le chemin (dossier + motif).


def find_rpms(rpm_dir):
    # os.path.join colle le dossier et le motif : "/opt/install/rpms" + "*.rpm".
    # -> "/opt/install/rpms/*.rpm".
    if not os.path.isdir(rpm_dir):
        raise FileNotFoundError ("Le dossier n'existe pas: "+ rpm_dir)
    motif = os.path.join(rpm_dir, "*.rpm")

    # glob.glob lit le disque et renvoie la liste des chemins qui collent au motif.
    # -> ["/opt/install/rpms/zabbix-agent.rpm", "/opt/install/rpms/postgresql.rpm", ...]
    fichiers = glob.glob(motif)

    # Garde-fou : le dossier existe, mais il est peut-être vide.

    # On renvoie cette liste à celui qui a appelé la fonction.
    return fichiers


resultat = find_rpms("C:/testrpms")
print(resultat)



