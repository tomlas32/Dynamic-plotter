import pymongo
from datetime import datetime
import credentials


client = pymongo.MongoClient(credentials.MONGO_URI)
db = client[credentials.DATABASE_NAME]
collection = db[credentials.COLLECTION_NAME]
collection1 = db[credentials.COLLECTION_NAME1]


# function for saving pressure data into databse
def store_measurements(
    user_id,
    sensor_type,
    experiment_name,
    instrument_id,
    protocol,
    cartridge_number,
    test_duration,
    measurements,
    notes,
):
    test_date = datetime.now().strftime("%Y-%m-%d")
    test_time = datetime.now().strftime("%H:%M:%S")

    record = {
        "test_date": test_date,
        "test_time": test_time,
        "user_id": user_id,
        "sensor_type": sensor_type,
        "instrument_id": instrument_id,
        "protocol": protocol,
        "experiment_name": experiment_name,
        "cartridge_number": cartridge_number,
        "test_duration": test_duration,
        "pressure_measurements": measurements,
        "notes": notes,
    }
    result = collection.insert_one(record)
    confirmation_msg = f"Session data inserted with ID: {result.inserted_id}"

    return confirmation_msg


# function for saving temp data into databse
def store_temp_measurements(
    user_id,
    sensor_type,
    experiment_name,
    instrument_id,
    protocol,
    cartridge_number,
    test_duration,
    measurements,
    notes,
):
    test_date = datetime.now().strftime("%Y-%m-%d")
    test_time = datetime.now().strftime("%H:%M:%S")

    record = {
        "test_date": test_date,
        "test_time": test_time,
        "user_id": user_id,
        "sensor_type": sensor_type,
        "instrument_id": instrument_id,
        "protocol": protocol,
        "experiment_name": experiment_name,
        "cartridge_number": cartridge_number,
        "test_duration": test_duration,
        "temp_measurements": measurements,
        "notes": notes,
    }
    result = collection1.insert_one(record)
    confirmation_msg = f"Session data inserted with ID: {result.inserted_id}"

    return confirmation_msg
