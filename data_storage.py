# data_storage.py

# Structure pour stocker les données de la trame
data = {}

def set_data(new_data):
    global data
    data = new_data

def get_data():
    return data
