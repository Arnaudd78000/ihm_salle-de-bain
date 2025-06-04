from flask import Flask, request
import time
from config import DEBUG
import data_storage
from ihm_main import IHM  # Importer la classe IHM du fichier ihm.py
from variable import etat_ble
import logging
import globals
logging.getLogger('werkzeug').disabled = True  # ← désactive les logs HTTP Flask

from logger import log
import globals

app = Flask(__name__)

class SERVEUR:
    def __init__(self, capteurs):
        #self.app_ihm = app_ihm  # Créer une instance de IHM ici, pas dans la fonction de route
        self.capteurs = capteurs
        # Enregistrer la route après l'initialisation
        app.add_url_rule('/rx_trame', 'recevoir_trame_HA', self.recevoir_trame_HA, methods=['POST'])
        app.add_url_rule('/rx_trame_pour_pico', 'recevoir_trame_to_pico_from_Nodered', self.recevoir_trame_to_pico_from_Nodered, methods=['POST'])


   # @app.route('/rx_trame', methods=['GET', 'POST'])
    def recevoir_trame_HA(self):
        log("RX: HA->SdB", fonction="F7")
        if request.is_json:
            data = request.get_json()

            # Stocker les données dans le module de stockage
            data_storage.set_data(data)

            # Afficher ou traiter les données comme nécessaire
            if DEBUG:
                print(f"Trame reçue : {data}")
        
            # Traite les données
            self.capteurs.traitement_rx_trame_HA()

            return "Trame HA reçue", 200
        else:
            return "Données non au format JSON", 400

    def to_bit(val):
        if isinstance(val, bool):
            return int(val)
        if isinstance(val, str):
            return 1 if val.lower() in ("true", "1") else 0
        if isinstance(val, int):
            return 1 if val == 1 else 0
        return 0

    # @app.route('/rx_trame_pour_pico', methods=['GET', 'POST'])
    def recevoir_trame_to_pico_from_Nodered(self):
        data = request.args.to_dict()
        # Afficher ou traiter les données comme nécessaire
        if DEBUG:
            print(f"Trame reçue : {data}")

        # Récupérer chaque élément (avec valeurs par défaut au cas où)
        # ATTENTION : chaine ble limitée à 20 carac et il y a 17 carac dans : T/18/19/0/0/0/21/18
        presence = 0 if data.get("presence", "False") == "False" else 1
        temp_pre_chauff = data.get("temp_pre_chauff", "17")
        temp_chauff = data.get("temp_chauff", "18")
        ordre_pre_chauff = 0 if data.get("ordre_pre_chauff", "False") == "False" else 1
        ordre_chauff = 0 if data.get("ordre_chauff", "False") == "False" else 1
        if ordre_chauff==0:
            if ordre_pre_chauff==0:
                globals.mode_chauff_chbre="off"
                globals.temp_cible_chbre=temp_pre_chauff
            else:
                globals.mode_chauff_chbre="on" #pre_chauff
                globals.temp_cible_chbre=temp_pre_chauff
        else:
            globals.mode_chauff_chbre="boost" #chauff
            globals.temp_cible_chbre=temp_chauff

        self.capteurs.app_ihm.refresh_icon_chauff()
        
        heure = data.get("heure", "00")
        minute = data.get("minute", "00")

        # Rempli etat_ble ce qui enverra un msg ble
        toto = f"{presence},{round((float(temp_pre_chauff)-16)*2)},{round((float(temp_chauff)-16)*2)},{globals.mode_debug_pico},{ordre_pre_chauff},{ordre_chauff},{heure},{minute}"
        etat_ble["envoyer"]=toto
        log(f"RXp: Nodered->SdB=>ble->pico: {toto}", fonction="F4")

        return "Trame HA reçue", 200      

    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)  # Écoute sur le port 8080


