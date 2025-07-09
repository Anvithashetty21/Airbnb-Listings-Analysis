from pymongo import MongoClient
import pandas as pd

def fetch_listings(limit=1000):
    client = MongoClient("mongodb://localhost:27017/")
    cursor = client["airbnb_project"]["listings"].find().limit(limit)
    df = pd.DataFrame(list(cursor))
    return df

if __name__ == "__main__":
    df = fetch_listings(5)
    print(df.head())
    print(df.columns)
