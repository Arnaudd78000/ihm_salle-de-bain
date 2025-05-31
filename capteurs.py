import os
import glob
import time
#import RPi.GPIO as GPIO
from config import DEBUG
from gpiozero import Button
import subprocess
import requests
import threading
import time
import data_storage
from variable import etat_ble
from datetime import datetime
import globals
#######
## à mettre partout
#######
# Redéfinir print partout
import builtins
from logger import log
builtins.print = log

# Numéro de la broche GPIO utilisée (BCM)
IRQ_PIN = 26  # capteur lum
DEBOUNCE_TIME = 0.2  # Temps anti-rebond en secondes (200 ms)

# Chemin du capteur DS18B20
base_dir = "/sys/bus/w1/devices/"
device_folder = glob.glob(base_dir + "28*")[0]  # Recherche le capteur
device_file = device_folder + "/w1_slave"

def send_1st_frame_to_nodered():
    url = "http://192.168.1.10:1990/nodered/pico_chbre_init"

    print("TX trame Nodered")

    try:
        response = requests.get(url)
        print("Code HTTP tx nodered:", response.status_code)
        response.close()
    except Exception as e:
        print("Erreur lors de la requete :", e)

ctr=0
ctr_meteo = 0

class CAPTEURS:
    def __init__(self, app_ihm):

        self.mode_test="2" #pas de test
        self.mode_test_old="2"
        
        self.app_ihm = app_ihm
        # Création de l'objet Button avec gestion des interruptions et debounce
        self.irq_button = Button(IRQ_PIN, bounce_time=DEBOUNCE_TIME) # capteur lum
        # Détection des interruptions avec debounce
        self.irq_button.when_pressed = self.on_falling   # Déclenché sur front descendant
        self.irq_button.when_released = self.on_rising   # Déclenché sur front montant
        self.lumiere="off"
        self.timer_5_ou_30_min(app_ihm)
        send_1st_frame_to_nodered()

    def test_wifi(self):
        commande = 'iwgetid'
        # Exécute la commande et capture la sortie
        result = subprocess.run(commande, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Assurez-vous que la sortie est bien une chaîne de caractères
        wifi_output = result.stdout.decode('utf-8').strip()

        if("Livebox-CBE6" in wifi_output):
            print("wifi OK")
            #self.app_ihm.icon_wifi_sdb.config(image=self.app_ihm.icon_wifi_on)
        else:
            self.app_ihm.canvas_sdb.delete(self.app_ihm.icon_wifi_on)
            self.icon_wifi_off_sdb = self.canvas_sdb.create_image(50, 12, image=self.icon_wifi_off)

            commande='rfkill block wifi'
            subprocess.run(commande, shell=True, check=True)
            print("wifi KO !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            time.sleep(5)
            commande='rfkill unblock wifi'
            subprocess.run(commande, shell=True, check=True)
            time.sleep(10)
            # Exécute la commande et capture la sortie
            result = subprocess.run(commande, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            wifi_output = result.stdout.decode('utf-8').strip()
            if("Livebox-CBE6" in wifi_output):
                print("wifi OK")
                self.app_ihm.canvas_sdb.delete(self.app_ihm.icon_wifi_off)
                self.icon_wifi_on_sdb = self.canvas_sdb.create_image(50, 12, image=self.icon_wifi_on)     
                send_1st_frame_to_nodered()


    def timer_5_ou_30_min(self, app_ihm):
        print("Timer")
        etat = self.read_lumiere()
        temp_c = self.read_temp()
        self.tx_trame_SdB_to_HA(temp_c, etat)

        self.test_wifi()

        # Mettre à jour la température de l'IHM
        app_ihm.update_temp_sdb(temp=temp_c)

        if DEBUG:
            print("Exécution de la fonction toutes les 5 minutes")

        if etat=="on":
            threading.Timer(300, self.timer_5_ou_30_min, args=[app_ihm,]).start() # 5min
        else:
            threading.Timer(1800, self.timer_5_ou_30_min, args=[app_ihm,]).start() # 30min

    ###############################################
    def timer_10_sec(self):
        global ctr_meteo, etat_ble

        if etat_ble["change"]==True:
            etat_ble["change"]=False
            if etat_ble["connecte"]==True:
                print("ble connexion change to : connected")
                self.app_ihm.canvas_chbre.delete(self.app_ihm.icon_wifi_off_chbre)
                self.app_ihm.icon_ble_on_chbre = self.app_ihm.canvas_chbre.create_image(50, 12, image=self.app_ihm.icon_ble_on) 
            else:
                print("ble connexion change to : disconnected")
                self.app_ihm.canvas_chbre.delete(self.app_ihm.icon_ble_on_chbre)
                self.app_ihm.icon_wifi_off_chbre = self.app_ihm.canvas_chbre.create_image(50, 12, image=self.app_ihm.icon_wifi_off) 

        # if etat_ble["rx"]==True:
        #     etat_ble["rx"]=False
        #     self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.text_temp_chbre, text=f"{etat_ble['temp']}°C")
        #     if etat_ble["mode"]=="off_0":
        #         self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.text_temp_cible_chbre, text="- °C")
        #         self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.icon_heat_salon , image=self.app_ihm.icon_radiator)
        #     else:               
        #         self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.text_temp_cible_chbre, text=f"{etat_ble['temp_cible']}°C")
        #         self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.icon_heat_chbre , image=self.app_ihm.icon_radiator_red)             

        if ctr_meteo==0:
            ctr_meteo=1
            self.app_ihm.label_meteo.config(image=self.app_ihm.meteo_img)
            self.app_ihm.label_t_ext.config(text=f"{self.app_ihm.current_temperature:.0f}°C")
            self.app_ihm.label_time_forecast.grid_remove()

        else:
            ctr_meteo=0
            self.app_ihm.label_meteo.config(image=self.app_ihm.meteo_forecast_img)
            self.app_ihm.label_t_ext.config(text=f"{self.app_ihm.forcecast_temperature:.0f}°C")
            self.app_ihm.label_time_forecast.config(image=self.app_ihm.icon_time_forecast)
            self.app_ihm.label_time_forecast.grid()


        etat = self.read_lumiere()
        if etat=="on":
            threading.Timer(10, self.timer_10_sec).start() # 10s

    ###############################################
    def tx_trame_SdB_to_HA(self, temp_c, etat):
        global ctr

        print(datetime.now().strftime("%H:%M") + "-TX: SdB->HA")
        # Configuration
        HA_URL = "http://192.168.1.10:8123"  # Remplace par l'URL de ton Home Assistant
        HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhYWNlODg0YzVkZTc0MzExYmI4MjA0ZGU1OWJhMzQ2NiIsImlhdCI6MTcxOTY0Njg3MiwiZXhwIjoyMDM1MDA2ODcyfQ.VKcX3OgWZ8vwLMI2odUXMs9mi9IYOHsV7ldTbwtl44s"

        ctr+=1
        value=f"{temp_c:.1f}/{etat}/{ctr}"

        if DEBUG:
            print(f"Data tx : {value}")

        # En-têtes de la requête
        HEADERS = {  "Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json" }
        # Corps de la requête
        data = { "state": value }
        # Envoi de la requête à Home Assistant
        try:
            response = requests.post(f"{HA_URL}/api/states/input_text.msg_from_sdb", json=data, headers=HEADERS)
        except:
            print(f"ERREUR: Impossible de contacter Home Assistant POUR CAPTEUR LUM : ({e})")
        #print(f"reponse:{response.status_code}")

    ###############################################
    def on_rising(self):
        self.lumiere="on"
        if DEBUG:
            print("🔼 Front montant détecté !")
        temp_c = self.read_temp()
        self.tx_trame_SdB_to_HA(temp_c, 1)
        commande='echo "performance"| sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'
        subprocess.run(commande, shell=True, check=True)

        self.app_ihm.update_meteo()
        self.app_ihm.icon_forecast_choice()

        self.timer_10_sec()

        # commande='DISPLAY=:0 xset dpms force on' #'xset dpms force on'
        # subprocess.run(commande, shell=True, check=True)

    ###############################################
    def on_falling(self):
        self.lumiere="off"
        if DEBUG:
            print("🔽 Front descendant détecté !")
        temp_c = self.read_temp()
        self.tx_trame_SdB_to_HA(temp_c, 0)
        commande='echo "powersave"| sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'
        subprocess.run(commande, shell=True, check=True)
        # commande='DISPLAY=:0 xset dpms force off' #'xset dpms force off'
        # subprocess.run(commande, shell=True, check=True)

    ###############################################
    def read_temp_raw(self):
        """Lit les données brutes du capteur."""
        with open(device_file, "r") as f:
            return f.readlines()
        
    ###############################################
    def read_temp(self):
        """Extrait et retourne la température en Celsius et Fahrenheit."""
        lines = self.read_temp_raw()
        while lines[0].strip()[-3:] != "YES":
            time.sleep(0.2)
            lines = self.read_temp_raw()
        
        equals_pos = lines[1].find("t=")
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
    ###############################################
    def read_lumiere(self):
        # Lecture de l'état du GPIO
        #etat = GPIO.input(26)
        etat=self.lumiere
        return etat
    
    ###############################################
    ###### Traitement Rx trame
    ###############################################
    def traitement_rx_trame_HA(self):
        # Récupérer les données stockées
        data = data_storage.get_data()
        #print(data)
        
        # Traitement des données
        if data:
            globals.mode_debug_pico=False if data.get("mode_test")=="2" else True
            self.app_ihm.label_icon_alerte.config(bg="orange" if data.get("alerte") == "on" else "grey")
            self.app_ihm.label_icon_message.config(bg="red" if data.get("message") == "on" else "grey")
            if(data.get("alarme")=="on"):
                self.app_ihm.label_icon_alarme.config(bg="red", image=self.app_ihm.icon_alarme)
            else:
                self.app_ihm.label_icon_alarme.config(bg="green" if data.get("presence") == "on" else "grey")
                self.app_ihm.label_icon_alarme.config(image=self.app_ihm.icon_home)
            if(data.get("pluie")=="Temps sec"):
                self.app_ihm.label_icon_pluie.config(image=self.app_ihm.icon_pluie1)
            elif(data.get("pluie")=="Pluie légère"):
                self.app_ihm.label_icon_pluie.config(image=self.app_ihm.icon_pluie2)
            else:
                self.app_ihm.label_icon_pluie.config(image=self.app_ihm.icon_pluie3)
            # salon
            self.app_ihm.canvas_salon.itemconfig(self.app_ihm.text_temp_salon, text=f"{data.get('temp_salon', '-')}°C") # Si 'temp_chbre' est None, cela retournera "-"
            temp=data.get('temp_cible_salon', '-')
            if temp=="0":
                temp="-"
            self.app_ihm.canvas_salon.itemconfig(self.app_ihm.text_temp_cible_salon, text=f"{temp}°C")
            if (data.get("mode_salon")=="OFF"):
                self.app_ihm.canvas_salon.itemconfig(self.app_ihm.icon_heat_salon , image=self.app_ihm.icon_radiator)
            else:
                self.app_ihm.canvas_salon.itemconfig(self.app_ihm.icon_heat_salon , image=self.app_ihm.icon_radiator_red)
            # chbre
            # gérer par rx pico
            # if data.get('temp_cible_chbre')!="None":
            #     self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.text_temp_chbre, text=f"{data.get('temp_chbre', '-')}°C")
            #     self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.text_temp_cible_chbre, text=f"{data.get('temp_cible_chbre', '-')}°C")
            #     self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.icon_heat_salon , image=self.app_ihm.icon_radiator)
            # else:
            #     self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.text_temp_chbre, text="- °C")
            #     self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.text_temp_cible_chbre, text="- °C")
            # if ((data.get("mode_chbre")=="off_0") or (data.get("mode_chbre")=="None")):
            #     self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.icon_heat_chbre , image=self.app_ihm.icon_radiator)
            # else:
            #     self.app_ihm.canvas_chbre.itemconfig(self.app_ihm.icon_heat_chbre , image=self.app_ihm.icon_radiator_red)
            # sdb
            if (data.get("mode_sdb")=="on"):
                self.app_ihm.canvas_sdb.itemconfig(self.app_ihm.icon_heat_sdb , image=self.app_ihm.icon_radiator_red)
            else:
                self.app_ihm.canvas_sdb.itemconfig(self.app_ihm.icon_heat_sdb , image=self.app_ihm.icon_radiator)


            self.mode_test=data.get("mode_test") # 2: pas de test, 1: etat_cpateur=on, 0: etat capteur=off
            if(self.mode_test_old!=self.mode_test):
                self.mode_test_old=self.mode_test
                if(self.mode_test=="1"):
                    self.on_rising()
                if(self.mode_test=="0"):
                    self.on_falling()
            # if (data.get("shutdown")=="on"):
            #     commande='shutdown'
            #     subprocess.run(commande, shell=True, check=True)


# Boucle principale
if __name__ == "__main__":
    capteurs = CAPTEURS()
    while True:
        temp_c = capteurs.read_temp()
        print(f"Température : {temp_c:.1f}°C")
        time.sleep(1)  # Rafraîchir toutes les secondes
        etat = capteurs.read_lumiere()
        print(f"État du GPIO 26 : {etat}")

