import pymongo
from datetime import datetime
import credentials


client = pymongo.MongoClient(credentials.MONGO_URI)
db = client[credentials.DATABASE_NAME]
collection = db[credentials.COLLECTION_NAME]


# function for saving data into databse
def store_measurements(self, measurements):
    test_date = datetime.now(datetime.timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
    experiment_name = self.exp_input.text()
    cartridge_number = self.sample_input.text()

    record = {
        "test_date": test_date,
        "experiment_name": experiment_name,
        "cartridge_number": cartridge_number,
        "measurements": measurements,
    }
    result = collection.insert_one(record)