import logging
import sys
from datetime import datetime
import glob
import os

logger = None  # Global logger utilisé dans `log()`

def init_logger():
    global logger

    if logger is not None:
        return logger  # Ne pas réinitialiser plusieurs fois

    logger = logging.getLogger("mon_logger")
    logger.setLevel(logging.DEBUG)


    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(BASE_DIR, "../ihm_sdb_log_files")
    os.makedirs(log_dir, exist_ok=True)

    # Nettoyage : ne garder que les 7 derniers fichiers
    log_files = sorted(
        glob.glob(os.path.join(log_dir, "logger_ihm_sdb_*.log")),
        key=os.path.getmtime,
        reverse=True
    )

    for old_file in log_files[7:]:  # Conserve les 7 plus récents
        try:
            os.remove(old_file)
        except Exception as e:
            print(f"Erreur lors de la suppression de {old_file} : {e}")

    # Création du fichier de log du jour
    date_str = datetime.now().strftime("%Y_%m_%d")
    log_filename = os.path.join(log_dir, f"logger_ihm_sdb_{date_str}.log")


    # Handler fichier
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Format
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    #console_handler.setFormatter(formatter)

    # Ajout des handlers
    logger.addHandler(file_handler)
    #logger.addHandler(console_handler)

    return logger

# log et print en meme temps
def log(*args, fonction=None):
    if logger is None:
        raise RuntimeError("Logger not initialized. Call init_logger() first.")
    
    message = " ".join(str(arg) for arg in args)
    heure = datetime.now().strftime("%H:%M")

    if fonction is None:
        logger.info(f"Fx: [{heure}] {message}")
    else:
        logger.info(f"{fonction}: [{heure}] {message}")

    print(message)
