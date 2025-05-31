# pour recharger ; sudo systemctl restart mon_script.service

import tkinter as tk #sudo apt-get install python3-tk
from ihm_main import IHM  # Importer la classe IHM depuis le fichier ihm.py
from serveur import SERVEUR
import threading
import sys
from config import DEBUG
from capteurs import CAPTEURS
import subprocess
import time
import requests
import asyncio
from bleak import BleakScanner, BleakClient, BleakError
import time
from variable import etat_ble
from datetime import datetime
from dotenv import load_dotenv
import os

# Charge les variables depuis .env
load_dotenv()
# Récupère le token
my_token = os.getenv("HA_TOKEN")

#######
## à mettre partout
#######
# Redéfinir print partout
import builtins
from logger import init_logger, log
builtins.print = log



UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

INACTIVITY_TIMEOUT = 80  # 20 minutes en secondes

global temp_pico_old
temp_pico_old=0

# Lancer asyncio dans un thread séparé
def start_async_loop_ble(app_ihm):
    # ✅ Crée une nouvelle boucle propre au thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_ble_client(app_ihm))
    finally:
        loop.close()

async def run_ble_client(app_ihm):
    global etat_ble

    while True:  # Boucle de reconnexion
        print("🔍 Recherche du PicoBLE...")
        devices = await BleakScanner.discover()
        pico = next((d for d in devices if "PicoBLE" in d.name), None)

        if not pico:
            print("❌ Pico introuvable, réessaye dans 4 minutes...")
            if etat_ble["connecte"]==True:
                etat_ble["change"]=True
                etat_ble["connecte"]=False
            await asyncio.sleep(240)
            continue

        try:
            async with BleakClient(pico) as client:
                await asyncio.sleep(1)  # ← petite pause
                print("✅ Connecté à", pico.name)
                if etat_ble["connecte"]==False:
                    etat_ble["change"]=True
                    etat_ble["connecte"]=True

                last_msg_time = time.time()


                def rx_ble_handle_notification(_, data):
                    nonlocal last_msg_time 
                    global temp_pico_old
                    #save time
                    last_msg_time = time.time()
                    message=data.decode()
                    print(datetime.now().strftime("%H:%M") + "-RXp: ble->Tx ChauffPico@HA")
                    # Décomposer la string pour obtenir les valeurs
                    valeurs = message.split(',')

                    # Assigner les valeurs aux variables
                    da=float(valeurs[0])
                    if(temp_pico_old==da):
                        da=da+0.1 #besoin pour rafraichissement valeur updated de HA
                    temp = f"{round(da, 1):.1f}"
                    temp_pico_old=da
                    temp_cible = valeurs[1]
                    modetx = valeurs[2]
                    cde_regul = valeurs[3]
                    elapsed_time_regul_minutes = valeurs[4]

                    app_ihm.canvas_chbre.itemconfig(app_ihm.text_temp_chbre, text=f"{temp}°C")
                    if modetx=="off_0":
                        app_ihm.canvas_chbre.itemconfig(app_ihm.text_temp_cible_chbre, text="- °C")
                        app_ihm.canvas_chbre.itemconfig(app_ihm.icon_heat_salon , image=app_ihm.icon_radiator)
                    else:               
                        app_ihm.canvas_chbre.itemconfig(app_ihm.text_temp_cible_chbre, text=f"{temp_cible}°C")
                        app_ihm.canvas_chbre.itemconfig(app_ihm.icon_heat_chbre , image=app_ihm.icon_radiator_red)  


                    # Adresse de ton serveur Home Assistant (remplace par la bonne IP et le bon port)
                    HA_URL = "http://192.168.1.10:8123/api/states/sensor.chauff_pico"
                    # Ton long-lived access token (genere dans ton profil Home Assistant)

                    # Donnees à envoyer
                    data_to_tx = {
                        "state": temp,  # La valeur principale du capteur (ex: temperature actuelle)
                        "attributes": {
                            "temp": temp,
                            "temp_cible": temp_cible,
                            "mode": modetx,
                            "regul": cde_regul,
                            "timeInRegul": elapsed_time_regul_minutes,
                            "unit_of_measurement": "C",  # 👈 Ajout de l'unite pour indiquer que c'est une temperature
                            "device_class": "temperature"  # 👈 Indique que c'est un c
                        }
                    }

                    # Envoi de la requete POST
                    headers = {
                        "Authorization": f"Bearer {my_token}",
                        "Content-Type": "application/json"
                    }

                    try:
                        # Envoi de la requête à Home Assistant
                        response = requests.post(HA_URL, json=data_to_tx, headers=headers)
                        if response.status_code==200:
                            print(f"    -> Tx ChauffPico@HA OK:", message)
                        else:
                            print(f"    -> Tx ChauffPico@HA KO !!!")
                    except requests.exceptions.RequestException as e:
                        print(f"        -> ERREUR: Impossible de contacter Home Assistant ({e})")

                # sur rx messasge, appellera : rx_ble_handle_notification
                await client.start_notify(TX_CHAR_UUID, rx_ble_handle_notification)

                # async def monitor_inactivity():
                #     while client.is_connected:
                #         if time.time()-last_msg_time > INACTIVITY_TIMEOUT:
                #             print("⏱️ Inactivité détectée. Déconnexion...")
                #             await client.disconnect()
                #             break
                #         await asyncio.sleep(10)

                async def send_loop():
                    while client.is_connected:
                        if etat_ble["envoyer"]:
                            #message = "1" # input(">> Message à envoyer : ")
                            try:
                                await client.write_gatt_char(RX_CHAR_UUID, etat_ble["envoyer"].encode())
                                etat_ble["envoyer"]=None
                            except Exception as e:
                                print("❌ Erreur d'envoi :", e)
                        await asyncio.sleep(10)

                await asyncio.gather(
                    # monitor_inactivity(),
                    send_loop()
                )

        except asyncio.TimeoutError as e:
            print(f"❌ Timeout lors de la connexion à {pico.name}: {e}")
            print("🔁 Tentative de reconnexion dans 4 minutes...")

        except BleakError as e:
            print(f"❌ Erreur de connexion : {e}")
            print("🔁 Tentative de reconnexion dans 4 minutes...")
            if etat_ble["connecte"]==True:
                etat_ble["change"]=True
                etat_ble["connecte"]=False
            await asyncio.sleep(240)

# Fonction qui lance le serveur Flask
def lancer_serveur():
    from serveur import app  # Importer l'application Flask depuis serveur.py
    app.run(host='0.0.0.0', port=8080)  # Lancer le serveur Flask

# Fonction principale qui démarre le serveur dans un thread
def main():
    init_logger()  # Obligatoire au lancement
    log("################################################")
    log("### Démarrage de l'application")
    log("################################################")

    # Autres tâches que tu souhaites effectuer dans main.py
    print("Main.py est en cours d'exécution.")
    root = tk.Tk()
    root.title("MAIN IHM")
    root.geometry("640x200")
    # Mettre la fenêtre toujours au premier plan
    root.attributes('-topmost', 1)
    app_ihm = IHM(root)  # Créer l'instance IHM
 
    capteurs=CAPTEURS(app_ihm)

    serveur = SERVEUR(capteurs)  # Créer l'instance SERVEUR avec root
    # Créer un thread pour exécuter la fonction lancer_serveur
    serveur_thread = threading.Thread(target=lancer_serveur)
    serveur_thread.daemon = True  # Permet au thread de se fermer avec le programme principal
    serveur_thread.start()  # Démarrer le thread

    # Lancer la boucle asyncio ble dans un thread à part
    threading.Thread(target=start_async_loop_ble, args=(app_ihm,), daemon=True).start()

    # # enleve le curseur
    # commande='unclutter &'
    # subprocess.run(commande, shell=True, check=True)

    root.mainloop()


if __name__ == "__main__":
    main()
