import json
import os
import psycopg2
from dotenv import load_dotenv

def parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.connection = None
        self.cursor = None

    def connect(self):
        """Connect to the PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                host=os.getenv("DB_HOSTNAME"),
                port=os.getenv("DB_PORT"),
                user=os.getenv("DB_USERNAME"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME")
            )
            self.cursor = self.connection.cursor()
            print("Database connection established.")
        except Exception as e:
            print(f"Error connecting to database: {e}")

    def fill_table(self):
        with open('utah_properties_20250816_223523.json', 'r') as f:
            properties = json.load(f)

        for prop in properties:
            price = prop.get('price').replace('$', '').replace(',', '')
            price = parse_int(price)
            beds = parse_int(prop.get('beds'))
            baths = parse_int(prop.get('baths'))
            sqft = parse_int(prop.get('sqft'))
            days_on_market = 0
            if prop.get('days_on_market') != "Listed":
                days_on_market = parse_int(prop.get('days_on_market'))
            else:
                days_on_market = 0
            self.cursor.execute("""
            INSERT INTO listings (mls_id, price, address, beds, baths, sqft, status, agent_name, agent_company, days_on_market, scraped_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
        prop.get('mls_id'),
        price,
        prop.get('address'),
        beds,
        baths,
        sqft,
        prop.get('status'),
        prop.get('agent_name'),
        prop.get('agent_company'),
        days_on_market,
        prop.get('scraped_at')
    ))
        self.connection.commit()
        self.cursor.close()
        self.connection.close()
if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.connect()
    db_manager.fill_table()