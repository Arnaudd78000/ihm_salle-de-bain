import asyncio
from bleak import BleakScanner, BleakClient, BleakError
import time

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

INACTIVITY_TIMEOUT = 80  # 20 minutes en secondes

async def run_ble_client():
    while True:  # Boucle de reconnexion
        print("🔍 Recherche du PicoBLE...")
        devices = await BleakScanner.discover(timeout=10)
        pico = next((d for d in devices if "PicoBLE" in d.name), None)

        if not pico:
            print("❌ Pico introuvable, réessaye dans 10 minutes...")
            await asyncio.sleep(5)
            continue

        try:
            async with BleakClient(pico) as client:
                print("✅ Connecté à", pico.name)

                last_msg_time = time.time()

                def handle_notification(_, data):
                    nonlocal last_msg_time
                    last_msg_time = time.time()
                    print("📨 Message reçu :", data.decode())

                # sur rx messasge, appellera : handle_notification
                await client.start_notify(TX_CHAR_UUID, handle_notification)

                async def monitor_inactivity():
                    while client.is_connected:
                        if time.time()-last_msg_time > INACTIVITY_TIMEOUT:
                            print("⏱️ Inactivité détectée. Déconnexion...")
                            await client.disconnect()
                            break
                        await asyncio.sleep(10)

                async def send_loop():
                    while client.is_connected:
                        message = "1" # input(">> Message à envoyer : ")
                        try:
                            await client.write_gatt_char(RX_CHAR_UUID, message.encode())
                        except Exception as e:
                            print("❌ Erreur d'envoi :", e)
                        await asyncio.sleep(10)

                await asyncio.gather(
                    monitor_inactivity(),
                    send_loop()
                )

        except BleakError as e:
            print(f"❌ Erreur de connexion : {e}")
            print("🔁 Tentative de reconnexion dans 5 secondes...")
            await asyncio.sleep(10)

# Démarrage de la boucle d'exécution
asyncio.run(run_ble_client())
