"""Chargement du fichier de config qui pilote l'orchestrateur (main.py)."""

import json
import os


def load_config(path="config.json"):
    if not os.path.isfile(path):
        raise FileNotFoundError("Fichier de config introuvable: " + path)

    with open(path) as f:
        return json.load(f)
