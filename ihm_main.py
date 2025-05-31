# ihm.py
import tkinter as tk
import time
from tkinter import PhotoImage
import requests
from PIL import Image, ImageDraw, ImageFont, ImageTk
from config import DEBUG
import data_storage
from datetime import datetime, timedelta
import customtkinter as ctk
from customtkinter import CTkImage

#######
## à mettre partout
#######
# Redéfinir print partout
import builtins
from logger import log
builtins.print = log
import globals

API_KEY = "eb226d2653ed00e8c8952db6777a471b"
VILLE = "Versailles"
LATITUDE = "48.8566"  # Exemple pour Paris
LONGITUDE = "2.3522"

# Initialiser la bibliothèque (recommandé)
ctk.set_appearance_mode("dark")  # ou "light"
ctk.set_default_color_theme("blue")  # ou "green", "dark-blue", etc.

class IHM:
    def __init__(self, root):
        self.root = root
        self.root.title("Interface IHM")

        self.temp_12h=0
        self.temp_21h=0
        self.temp_6h=0
        self.mode_ihm="normal"

        # Chargement des icônes avec gestion des erreurs
        size_icon=4
        self.icon_message = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/message.png").subsample(size_icon, size_icon) 
        self.icon_alerte = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/alerte.png").subsample(size_icon, size_icon) 
        self.icon_alarme = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/alarme.png").subsample(size_icon, size_icon)
        self.icon_home = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/home.png").subsample(size_icon, size_icon)
        self.icon_meteo = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/meteo_default.png").subsample(2, 2)  # Image météo par défaut
        self.icon_pluie1 = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/water-off.png").subsample(8, 8)
        self.icon_pluie2 = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/water.png").subsample(8, 8)
        self.icon_pluie3 = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/water-alert.png").subsample(8, 8)
       # self.icon_bed = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/bed.png").subsample(4, 4)
        self.icon_radiator = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/radiator.png").subsample(10, 10)
        self.icon_radiator_red = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/radiator_red.png").subsample(10, 10)
        self.icon_now = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/now.png").subsample(1, 1)
        self.icon_6h = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/6h.png").subsample(1, 1)
        self.icon_12h = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/12h.png").subsample(1, 1)
        self.icon_21h = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/21h.png").subsample(1, 1)
        self.icon_wifi_on = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/wifi_on.png").subsample(12, 12)
        self.icon_wifi_off = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/wifi_off.png").subsample(16, 16)
        #self.icon_bed = PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/bed.png").zoom(1, 1)
        # self.icon_boost=PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/boost.png").subsample(3, 3)
        # self.icon_on=PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/on.png").subsample(3, 3)
        #self.icon_off=PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/off.png").subsample(3, 3)
        icon_off_pil = Image.open("/home/pi/Desktop/RASADA/ihm_sdb/Img/mdi_off.png")
        self.icon_off = CTkImage(light_image=icon_off_pil, size=(32, 32))  # ou autre taille
        icon_on_pil = Image.open("/home/pi/Desktop/RASADA/ihm_sdb/Img/mdi_on.png")
        self.icon_on = CTkImage(light_image=icon_on_pil, size=(32, 32))  # ou autre taille
        self.icon_plus=PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/plus.png").subsample(4, 4)
        self.icon_moins=PhotoImage(file="/home/pi/Desktop/RASADA/ihm_sdb/Img/moins.png").subsample(4, 4)
        # Frame principale
        self.frame_principal = tk.Frame(self.root, bg="black")
        self.frame_principal.grid(sticky="nsew")

        # # Ajustement automatique de la grille
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        #####################################
        # Frame de l'heure et icone 
        #####################################
        self.frame_ligne1 = tk.Frame(self.frame_principal, bg="black")
        self.frame_ligne1.grid(sticky="nsew")
        self.frame_heure = tk.Frame(self.frame_ligne1, bg="black")
        self.frame_heure.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        # self.frame_heure = tk.Frame(self.frame_principal, bg="black")
        # self.frame_heure.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Labels pour l'heure et le jour
        self.label_time = tk.Label(self.frame_heure, text="00:00", font=("Helvetica", 50), fg="white", bg="black")
        self.label_time.grid(row=0, column=0, pady=5)

        self.label_day = tk.Label(self.frame_heure, text="Lundi 01 Janvier", font=("Helvetica", 18), fg="gray", bg="black")
        self.label_day.grid(row=1, column=0 )
    
        # Frame des icônes
        self.frame_icons = tk.Frame(self.frame_heure, bg="black")
        self.frame_icons.grid(row=2, column=0, pady=10, padx=10, sticky="w")

        # textes et boutons dupliqués avec temp et reglage chauff chbre
        self.frame_moins_plus = tk.Frame(self.frame_heure, bg="black")
        self.frame_moins_plus.grid(row=0, column=0, pady=5)  
        self.label_icon_plus = ctk.CTkButton(
            self.frame_moins_plus,
            text="+",
            text_color="black",         # texte en rouge
            font=("Arial", 48, "bold") ,
            fg_color="grey",          # fond du bouton
            border_color="white",     # contour blanc
            border_width=0,
            corner_radius=10,         # arrondi
            width=75,                 # largeur du bouton
            height=65                 # hauteur du bouton
        )
        self.label_icon_moins = ctk.CTkButton(
            self.frame_moins_plus,
            text="-",
            text_color="black",         # texte en rouge
            font=("Arial", 48, "bold") ,
            fg_color="grey",          # fond du bouton
            border_color="white",     # contour blanc
            border_width=0,
            corner_radius=10,         # arrondi
            width=75,                 # largeur du bouton
            height=65                # hauteur du bouton
        )
        self.label_icon_plus.grid(row=0, column=0, padx=5)      
        self.label_icon_moins.grid(row=0, column=1, padx=15)   

        self.label_temp_cible_chbre = tk.Label(self.frame_heure, text="Target Temp = ", font=("Helvetica", 18), fg="gray", bg="black")
        self.label_temp_cible_chbre.grid(row=1, column=0)
        self.label_temp_cible_chbre.grid_remove()
        self.frame_moins_plus.grid_remove()


        #####################################
        # Frame météo(à droite)
        #####################################
        self.frame_meteo = tk.Frame(self.frame_ligne1, bg="grey")
        self.frame_meteo.grid(row=0, rowspan=2, column=1, padx=0, pady=0, sticky="e") #occupe 2 lignes avec rowspan=2

        self.label_meteo = tk.Label(self.frame_meteo, image=self.icon_meteo, bg="blue")
        self.label_meteo.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.label_t_ext = tk.Label(self.frame_meteo, text="19°C", font=("Helvetica", 28), fg="white", bg="blue")
        self.label_t_ext.grid(row=0, column=0, padx=20, pady=10, sticky="nw")
        self.label_tminmax = tk.Label(self.frame_meteo, text="19°C", font=("Helvetica", 18, "bold"), fg="black", bg="blue")
        self.label_tminmax.grid(row=0, column=0, padx=0, pady=5, sticky="s")
        self.label_icon_pluie = tk.Label(self.frame_meteo, image=self.icon_pluie1, fg="white", bg="white")
        self.label_icon_pluie.grid(row=0, column=0, padx=10, pady=10, sticky="ne")
        self.label_time_forecast = tk.Label(self.frame_meteo, image=self.icon_now, bg="blue")
        self.label_time_forecast.grid(row=0, column=0, padx=(5, 10), pady=20, sticky="w")
        #self.label_time_forecast.lift() # Forcer le label à être au premier plan


        #####################################
        # Frame icones Maison / Messages / Alertes
        #####################################
        # Création des Labels avec icônes
        self.label_icon_alarme = tk.Label(self.frame_icons, image=self.icon_home, bg="grey")
        self.label_icon_alarme.grid(row=0, column=0, padx=5)
        self.label_icon_message = tk.Label(self.frame_icons, image=self.icon_message, bg="grey")
        self.label_icon_message.grid(row=0, column=1, padx=5)
        self.label_icon_alerte = tk.Label(self.frame_icons, image=self.icon_alerte, bg="grey")
        self.label_icon_alerte.grid(row=0, column=2, padx=5)

        # Icones dupliquées avec OFF/ON/BOOST
        # self.label_icon_off = tk.Button(self.frame_icons, image=self.icon_off, bg="grey")
        # self.label_icon_off.grid(row=0, column=0, padx=5)

        self.label_icon_off = ctk.CTkButton(
            master=self.frame_icons,
            image=self.icon_off,
            text="",
            text_color="black",         # texte en rouge
            font=("Arial", 17, "bold") ,
            fg_color="grey",          # fond du bouton
            border_color="white",     # contour blanc
            border_width=4,
            corner_radius=10,         # arrondi
            width=75,                 # largeur du bouton
            height=70                 # hauteur du bouton
        )
        self.label_icon_off.grid(row=0, column=0, padx=5)
        self.label_icon_on = ctk.CTkButton(
            master=self.frame_icons,
            image=self.icon_on,
            text="",
            #compound="top",  # 👈 Place le texte sous l’image
            # text="ON",
            # text_color="green",         # texte en rouge
            font=("Arial", 12, "bold") ,
            fg_color="grey",          # fond du bouton
            border_color="white",     # contour blanc
            border_width=4,
            corner_radius=10,         # arrondi
            width=75,                 # largeur du bouton
            height=70                 # hauteur du bouton
        )
        self.label_icon_on.grid(row=0, column=1, padx=5)
        self.label_icon_boost = ctk.CTkButton(
            self.frame_icons,
            text="BOOST",
            text_color="red",         # texte en rouge
            font=("Arial", 17, "bold") ,
            fg_color="grey",          # fond du bouton
            border_color="white",     # contour blanc
            border_width=4,
            corner_radius=10,         # arrondi
            width=75,                 # largeur du bouton
            height=70                 # hauteur du bouton
        )
        self.label_icon_boost.grid(row=0, column=2, padx=5)

        #self.label_icon_on = tk.Button(self.frame_icons, image=self.icon_on, bg="grey")
        # self.label_icon_on.grid(row=0, column=1, padx=5)
        #self.label_icon_boost = tk.Button(self.frame_icons, image=self.icon_boost, bg="grey")
        #self.label_icon_boost.grid(row=0, column=2, padx=5)
        self.label_icon_off.grid_remove()
        self.label_icon_on.grid_remove()
        self.label_icon_boost.grid_remove()

        #####################################
        # Frame des pieces
        #####################################
        self.frame_temp_salon = tk.Frame(self.frame_principal, bg="#303030")
        self.frame_temp_salon.grid(row=3, column=0, padx=10, pady=10, sticky="ws")

        self.canvas_chbre = tk.Canvas(self.frame_temp_salon, width=150, height=90, bg=self.frame_temp_salon["bg"], highlightthickness=1, bd=0)
        self.canvas_chbre.grid(row=0, column=0)
        self.canvas_sdb = tk.Canvas(self.frame_temp_salon, width=150, height=90, bg=self.frame_temp_salon["bg"], highlightthickness=1, bd=0)
        self.canvas_sdb.grid(row=0, column=1)
        self.canvas_salon = tk.Canvas(self.frame_temp_salon, width=150, height=90, bg=self.frame_temp_salon["bg"], highlightthickness=1, bd=0)
        self.canvas_salon.grid(row=0, column=2)
        # Le cercle
        centre_x = -50  # Centre à gauche du canvas
        centre_y = 50  # Centre au milieu verticalement
        rayon = 125
        # Dessiner la partie visible du cercle
        self.oval_chbre = self.canvas_chbre.create_oval(centre_x-rayon, centre_y-rayon, 
                        centre_x + rayon, centre_y + rayon, 
                        fill="grey", outline="black")
        self.canvas_sdb.create_oval(centre_x-rayon, centre_y-rayon, 
                        centre_x + rayon, centre_y + rayon, 
                        fill="grey", outline="black")
        self.canvas_salon.create_oval(centre_x-rayon, centre_y-rayon, 
                        centre_x + rayon, centre_y + rayon, 
                        fill="grey", outline="black")
        ###############################################
        ### CHBRE
        self.text_temp_chbre=self.canvas_chbre.create_text(110, 20, text="19.5°C", font=("Helvetica", 18), fill="white")
        self.text_temp_cible_chbre=self.canvas_chbre.create_text(110, 45, text="18.5°C", font=("Helvetica", 14), fill="grey")
        self.icon_heat_chbre = self.canvas_chbre.create_image(110, 70, image=self.icon_radiator)
        self.icon_wifi_chbre = self.canvas_chbre.create_image(50, 12, image=self.icon_wifi_off)

        image_path = "/home/pi/Desktop/RASADA/ihm_sdb/Img/bed.png"
        image = Image.open(image_path)  # Ouvre l’image avec PIL
        new_size=(60, 60)
        resized_image = image.resize(new_size, Image.LANCZOS)
        self.icon_bed = ImageTk.PhotoImage(resized_image )
        self.canvas_chbre.create_image(35, 50, image=self.icon_bed)
        ###############################################
        ### SdB
        self.text_temp_sdb=self.canvas_sdb.create_text(110, 20, text="19.5°C", font=("Helvetica", 18), fill="white")
        #self.text_temp_cible_sdb=self.canvas_sdb.create_text(110, 45, text="18.5°C", font=("Helvetica", 14), fill="grey")
        self.icon_heat_sdb = self.canvas_sdb.create_image(110, 70, image=self.icon_radiator)
        self.icon_wifi_on_sdb = self.canvas_sdb.create_image(50, 12, image=self.icon_wifi_on)

        image_path = "/home/pi/Desktop/RASADA/ihm_sdb/Img/sdb.png"
        image = Image.open(image_path)  # Ouvre l’image avec PIL
        new_size=(60, 60)
        resized_image = image.resize(new_size, Image.LANCZOS)

        self.icon_sdb = ImageTk.PhotoImage(resized_image )
        self.canvas_sdb.create_image(35, 45, image=self.icon_sdb)
        ###############################################
        ### Salon       
        self.text_temp_salon = self.canvas_salon.create_text(110, 20, text="19.5°C", font=("Helvetica", 18), fill="white")
        self.text_temp_cible_salon =self.canvas_salon.create_text(110, 45, text="18.5°C", font=("Helvetica", 14), fill="grey")
        self.icon_heat_salon = self.canvas_salon.create_image(110, 70, image=self.icon_radiator)

        image_path = "/home/pi/Desktop/RASADA/ihm_sdb/Img/salon.png"
        image = Image.open(image_path) 
        new_size=(50, 50)
        resized_image = image.resize(new_size, Image.LANCZOS)
        self.icon_salon = ImageTk.PhotoImage(resized_image )
        self.canvas_salon.create_image(35, 50, image=self.icon_salon)
        
        #####################################
        # Mode plein écran avec Échap pour quitter
        #####################################
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda event: self.root.attributes('-fullscreen', False))

        # Mise à jour de l'heure & meteo
        self.update_time()
        self.update_meteo()
        # au démarrage, @5h30 seulement on rafraichit et sauvegrade les forecasts
        self.update_forecast_meteo()

        #####################################
        # Touch Screen
        #####################################
        # Lier le clic/touch à la fonction
        self.canvas_chbre.bind("<Button-1>", self.on_touch_chbre)
        self.label_icon_off.bind("<Button-1>", self.on_touch_chauff_off)
        self.label_icon_on.bind("<Button-1>", self.on_touch_chauff_on)
        self.label_icon_boost.bind("<Button-1>", self.on_touch_chauff_boost)
        self.label_icon_plus.bind("<Button-1>", self.on_touch_plus)
        self.label_icon_moins.bind("<Button-1>", self.on_touch_moins)
        # self.canvas_chbre.bind("<Button>", self.on_touch)
        # self.canvas_chbre.bind("<ButtonPress-1>", self.on_touch)
        # self.canvas_chbre.bind("<ButtonRelease-1>", self.on_touch)


    ###############################################
    def on_touch_chbre(self, event):
        print("Zone canvas chbre touchée !")
        if self.mode_ihm != "chbre":
            self.mode_ihm="chbre"
            self.label_icon_alarme.grid_remove()
            self.label_icon_alerte.grid_remove()
            self.label_icon_message.grid_remove()
            self.label_day.grid_remove()
            self.label_time.grid_remove()
            self.label_icon_off.grid()
            self.label_icon_on.grid()
            self.label_icon_boost.grid()
            self.label_temp_cible_chbre.grid()
            self.canvas_chbre.itemconfig(self.oval_chbre, fill="blue")
            self.frame_moins_plus.grid()

            self.refresh_icon_chauff()   
        else:
            self.mode_ihm="normal"
            self.canvas_chbre.itemconfig(self.oval_chbre, fill="grey")      
            self.label_icon_alarme.grid()
            self.label_icon_alerte.grid()
            self.label_icon_message.grid()
            self.label_day.grid()
            self.label_time.grid()
            self.label_icon_off.grid_remove()
            self.label_icon_on.grid_remove()
            self.label_icon_boost.grid_remove()
            self.label_temp_cible_chbre.grid_remove()
            self.frame_moins_plus.grid_remove()


    def on_touch_chauff_off(self, event):
        if globals.mode_chauff_chbre!="off":
            globals.mode_chauff_chbre="off" 
            self.refresh_icon_chauff()   
            self.tx_chauff_ordre_vers_nodered(globals.mode_chauff_chbre, "0")

    def on_touch_chauff_on(self, event):
        if globals.mode_chauff_chbre!="on":
            globals.mode_chauff_chbre="on" 
            self.refresh_icon_chauff() 
            self.tx_chauff_ordre_vers_nodered(globals.mode_chauff_chbre, "0")

    def on_touch_chauff_boost(self, event):
        if globals.mode_chauff_chbre!="boost":
            globals.mode_chauff_chbre="boost" 
            self.refresh_icon_chauff()
            self.tx_chauff_ordre_vers_nodered(globals.mode_chauff_chbre, "0")

    def on_touch_plus(self, event):
        self.tx_chauff_ordre_vers_nodered(globals.mode_chauff_chbre, "1")

    def on_touch_moins(self, event):
        self.tx_chauff_ordre_vers_nodered(globals.mode_chauff_chbre,"-1")

    def tx_chauff_ordre_vers_nodered(self, ma_demande, delta):
        url = "http://192.168.1.10:1990/nodered/pico_chbre?demande="+ma_demande+"&delta="+delta
        try:
            response = requests.get(url)
        except requests.RequestException as e:
            print("Erreur lors de la requête pico_chbre:", e)

    def refresh_icon_chauff(self):
        if globals.mode_chauff_chbre=="off":
            self.label_icon_off.configure(border_width=4)
            self.label_icon_on.configure(border_width=0)
            self.label_icon_boost.configure(border_width=0)
        elif globals.mode_chauff_chbre=="on":
            self.label_icon_off.configure(border_width=0)
            self.label_icon_on.configure(border_width=4)
            self.label_icon_boost.configure(border_width=0)           
        else:
            self.label_icon_off.configure(border_width=0)
            self.label_icon_on.configure(border_width=0)
            self.label_icon_boost.configure(border_width=4)
        self.label_temp_cible_chbre.config(text=f"Cible = {globals.temp_cible_chbre}°C")

    ###############################################
    def update_time(self):
        """Met à jour l'affichage de l'heure et du jour."""
        now = time.strftime("%H:%M")
        day = time.strftime("%A %d %B")

        self.label_time.config(text=now)
        self.label_day.config(text=day)

        self.root.after(1000, self.update_time)

    ###############################################
    def update_meteo(self):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={VILLE}&appid={API_KEY}&units=metric"

        response = requests.get(url)
        data = response.json()

        if "weather" in data:
            condition = data["weather"][0]["main"]
            icon_code = data["weather"][0]["icon"]
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}.png"
            
            # Télécharger l'image météo
            img_data = requests.get(icon_url).content
            with open("meteo.png", "wb") as handler:
                handler.write(img_data)

            # Afficher l'image
            img = Image.open("meteo.png")
            img = img.resize((170, 170))
            self.meteo_img = ImageTk.PhotoImage(img)
            
            # Ajouter la température
            self.current_temperature = data["main"]["temp"]

            # tmax = round(data["main"]["temp_max"],0)
            # self.label_tminmax.config(text=f"{tmin:.0f}°C / {tmax:.0f}°C")

            url = "https://webservice.meteofrance.com/forecast?lat=48.808193&lon=2.12667&token=__Wj7dVSTjV9YGu1guveLyDq0g7S7TfTjaHBTPTpO0kj8__"
            response = requests.get(url)
            data = response.json() 
            #chemin = payload.daily_forecast[0].T.min
            forecast_today = data["daily_forecast"]
            firstday=forecast_today[0]
            temp=firstday["T"]["min"]
            tmin = round(float(temp), 0)
            temp=firstday["T"]["max"]
            tmax = round(float(temp), 0) 

            self.label_tminmax.config(text=f"{tmin:.0f}°C / {tmax:.0f}°C")

    #    self.root.after(600000, self.update_meteo)  # Actualisation toutes les 10 minutes

    ###############################################
    def update_forecast_meteo(self):
        # URL pour les prévisions météo sur 5 jours (avec des mises à jour toutes les 3 heures)
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={VILLE}&appid={API_KEY}&units=metric"

        response = requests.get(url)
        data = response.json()
        #print(data)
        # Vérifier que la réponse contient bien des prévisions
        if "list" in data:
            # Trouver l'entrée correspondante à 12 heures (les prévisions sont toutes les 3 heures)
            # Obtenir la date du jour au format yyyy-mm-dd
            date_du_jour = datetime.now().strftime("%Y-%m-%d")
            heure = int(datetime.now().strftime("%H"))
            # Construire la chaîne de l'heure voulue
            #heure_voulue = "2025-04-06 18:00:00"
            if(heure<=10):
                heure_voulue = f"{date_du_jour} 12:00:00"
                for bloc in data["list"]:
                    if bloc["dt_txt"] == heure_voulue:
                        icon_code = bloc["weather"][0]["icon"]
                        self.icon_code_12h = icon_code
                        self.temp_12h = bloc["main"]["temp"]
                        print(f"Icone à {heure_voulue} : {icon_code}")
                        break
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}.png"
                # Télécharger l'image météo
                img_data = requests.get(icon_url).content
                with open("meteo_12h.png", "wb") as handler:
                    handler.write(img_data)

            if(heure<=19):
                heure_voulue = f"{date_du_jour} 21:00:00"
                for bloc in data["list"]:
                    if bloc["dt_txt"] == heure_voulue:
                        icon_code = bloc["weather"][0]["icon"]
                        self.icon_code_21h = icon_code
                        self.temp_21h = bloc["main"]["temp"]
                        print(f"Icone à {heure_voulue} : {icon_code}")
                        print(f"temp @21h: {self.temp_21h}")
                        break
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}.png"
                # Télécharger l'image météo
                img_data = requests.get(icon_url).content
                with open("meteo_21h.png", "wb") as handler:
                    handler.write(img_data)

            demain = datetime.now() + timedelta(days=1)
            heure_voulue = demain.strftime("%Y-%m-%d") + " 06:00:00"                   
            for bloc in data["list"]:
                if bloc["dt_txt"] == heure_voulue:
                    icon_code = bloc["weather"][0]["icon"]
                    self.icon_code_6h = icon_code
                    self.temp_6h = bloc["main"]["temp"]
                    print(f"Icone à {heure_voulue} : {icon_code}")
                    break
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}.png"
            # Télécharger l'image météo
            img_data = requests.get(icon_url).content
            with open("meteo_6h.png", "wb") as handler:
                handler.write(img_data)

    ###############################################
    def icon_forecast_choice(self):
        heure = datetime.now().hour
        if(heure<=10):
            file="meteo_12h.png"
            self.forcecast_temperature=self.temp_12h
            print("choix=12h")
            self.icon_time_forecast=self.icon_12h
        elif (heure<19):
            file="meteo_21h.png"
            self.forcecast_temperature=self.temp_21h
            print("choix=21h")
            self.icon_time_forecast=self.icon_21h
        else:
            file="meteo_6h.png"
            self.forcecast_temperature=self.temp_6h
            print("choix=6h")
            self.icon_time_forecast=self.icon_6h

        img = Image.open(file)
        img = img.resize((170, 170))
        self.meteo_forecast_img = ImageTk.PhotoImage(img)
        
    ###############################################
    def update_temp_sdb(self, temp):
        self.canvas_sdb.itemconfig(self.text_temp_sdb, text=f"{temp:.1f}°C")

# Exécuter seulement si ce fichier est lancé directement
def start_app():
    root = tk.Tk()
    app = IHM(root)
    root.mainloop()

if __name__ == "__main__":
    start_app()
