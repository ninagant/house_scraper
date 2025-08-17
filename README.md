# Utah Real Estate Scraper

This project scrapes property listings from [utahrealestate.com](https://www.utahrealestate.com) for South Jordan, UT, and saves the results to CSV, JSON, and a PostgreSQL database.

## Features
- Uses Selenium to automate browser actions and extract property data
- Extracts details such as MLS ID, price, address, beds, baths, sqft, status, agent info, and days on market
- Saves results to CSV and JSON files
- Loads data into a PostgreSQL database using psycopg2
- Uses environment variables for database credentials via `.env` and `python-dotenv`

## Project Structure
- `scraper.py`: Main web scraper for property listings
- `database_creation.py`: Loads JSON data into PostgreSQL
- `db.sql`: SQL schema for the `listings` table
- `requirements.txt`: Python dependencies
- `.env`: Database credentials (not tracked in version control)
- `utah_properties_*.csv` / `utah_properties_*.json`: Scraped data files

## Setup
1. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
2. **Set up PostgreSQL database**
   - Create a database and user if needed
   - Run `db.sql` to create the `listings` table
   - Fill out `.env` with your database credentials:
     ```
     DB_HOSTNAME=localhost
     DB_PORT=5432
     DB_USERNAME=your_db_user
     DB_PASSWORD=your_db_password
     DB_NAME=your_db_name
     ```
3. **Run the scraper**
   ```sh
   python scraper.py
   ```
   This will save results to CSV and JSON files.
4. **Load data into PostgreSQL**
   ```sh
   python database_creation.py
   ```

## Notes
- The scraper is tailored for South Jordan, UT, but can be modified for other locations.
- Make sure Chrome and chromedriver are installed and compatible with Selenium.
- The project uses headless Chrome by default; set `headless=False` in `scraper.py` to see browser actions.
