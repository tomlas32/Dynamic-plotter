import pymongo
from datetime import datetime
import credentials


client = pymongo.MongoClient(credentials.MONGO_URI)
db = client[credentials.DATABASE_NAME]
collection = db[credentials.COLLECTION_NAME]


# function for saving data into databse
def store_measurements(experiment_name, cartridge_number, measurements):
    test_date = datetime.now().strftime("%Y-%m-%d")

    record = {
        "test_date": test_date,
        "experiment_name": experiment_name,
        "cartridge_number": cartridge_number,
        "measurements": measurements,
    }
    result = collection.insert_one(record)
    confirmation_msg = f"Session data inserted with ID: {result.inserted_id}"

    return confirmation_msg
