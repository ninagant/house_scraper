from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import csv
import json
import re
from datetime import datetime

class UtahRealEstateScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome options"""
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent to look more like a real browser
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = None
        self.wait = None
        
    def start_driver(self):
        """Start the Chrome driver"""
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
        
    def navigate_to_search(self, location="South Jordan, UT"):
        """Navigate to the search page for a specific location"""
        try:
            # Go to the grid view search page
            url = "https://www.utahrealestate.com"
            self.driver.get(url)
            
            print(f"Navigated to: {url}")
            
            # Wait for page to load completely
            time.sleep(5)

            # Check if we need to set location (this might vary based on the site's behavior)
            # You might need to interact with search fields if the default isn't South Jordan
            location_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='geolocation']")))
            location_input.clear()
            location_input.send_keys(location)
            location_input.send_keys(Keys.RETURN)
            print(f"Searching for properties in: {location}")

            # Wait for page to load completely
            time.sleep(5)

            # Find and click the grid view toggle button
            try:
                grid_view_btn = self.driver.find_element(By.CLASS_NAME, "toggle-btn-grid-view")
                grid_view_btn.click()
                print("Clicked grid view toggle button.")
                time.sleep(5)  # Wait for the page to update
            except Exception as e:
                print("Grid view toggle button not found or could not be clicked:", e)

            return True
            
        except Exception as e:
            print(f"Error navigating to search: {e}")
            return False
    
    def extract_property_data(self, property_li):
        """Extract data from a single property li element based on the HTML structure"""
        property_data = {
            'mls_id': None,
            'price': None,
            'address': None,
            'beds': None,
            'baths': None,
            'sqft': None,
            'status': None,
            'agent_name': None,
            'agent_company': None,
            'days_on_market': None,
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            # Extract MLS ID from the li element ID (e.g., "mls-inline-2105698")
            li_id = property_li.get_attribute('id')
            if li_id and 'mls-inline-' in li_id:
                property_data['mls_id'] = li_id.replace('mls-inline-', '')
            
            # Find the property card div
            property_card = property_li.find_element(By.CSS_SELECTOR, "div.property___card")
            
            # Extract price from div.list__price
            str_listing_details = ""
            try:
                price_element = property_card.find_element(By.CSS_SELECTOR, "div.list___price")
                property_data['price'] = price_element.text.strip()
                print(f"Found price: {property_data['price']}")
            except NoSuchElementException:
                print("Price not found")

            try:
                listing_details = property_card.find_element(By.CSS_SELECTOR, "div.listing___details.truncate")
                print(f"Found listing details: {listing_details}")
                str_listing_details = listing_details.find_element(By.TAG_NAME, "span").text.strip()
                print(f"Found str listing details: {str_listing_details}")
            except NoSuchElementException:
                print("Listing details not found")

            # Extract listing agent info if available
            try:
                listing_agents = property_card.find_element(By.CSS_SELECTOR, "div.listing___agent.truncate")
                str_listing_agents = listing_agents.find_element(By.TAG_NAME, "span").text.strip()
                print(f"Found str listing agents: {str_listing_agents}")
                if str_listing_agents:
                    agent_name_company = str_listing_agents.split('|')
                    if len(agent_name_company) > 0:
                        property_data['agent_name'] = agent_name_company[0].strip()
                    else:
                        property_data['agent_company'] = str_listing_agents

                    if len(agent_name_company) > 1:    
                        property_data['agent_company'] = agent_name_company[1].strip()
            except Exception:
                pass

            # Extract property details from the span (beds, baths, sqft)
            try:
                
                # Parse beds
                beds_match = re.search(r'(\d+)\s*bds?', str_listing_details, re.IGNORECASE)
                if beds_match:
                    property_data['beds'] = beds_match.group(1)
                
                # Parse baths
                baths_match = re.search(r'(\d+(?:\.\d+)?)\s*ba', str_listing_details, re.IGNORECASE)
                if baths_match:
                    property_data['baths'] = baths_match.group(1)
                
                # Parse square footage
                sqft_match = re.search(r'([\d,]+)\s*SqFt', str_listing_details, re.IGNORECASE)
                if sqft_match:
                    property_data['sqft'] = sqft_match.group(1).replace(',', '')
                    
            except NoSuchElementException:
                print("Property details span not found")
            
            # Extract address - look for address-related elements
            try:
                # The address might be in different locations, try multiple selectors
                address_selectors = [
                    "div.listing___address",
                    "[class*='address']",
                    ".property___address",
                    "div[class*='listing___address']"
                ]
                
                for selector in address_selectors:
                    try:
                        address_element = property_card.find_element(By.CSS_SELECTOR, selector)
                        property_data['address'] = address_element.text.strip()
                        print(f"Found address: {property_data['address']}")
                        break
                    except NoSuchElementException:
                        continue
                        
                # If no specific address element, try to extract from visible text
                if not property_data['address']:
                    # Look for text that looks like an address
                    all_text = property_card.text
                    lines = all_text.split('\n')
                    for line in lines:
                        if any(word in line.lower() for word in ['dr', 'st', 'ave', 'way', 'ln', 'ct', 'south jordan']):
                            property_data['address'] = line.strip()
                            break
                            
            except Exception as e:
                print(f"Error extracting address: {e}")
            
            # Extract status (Active, Pending, etc.)
            try:
                status_element = property_card.find_element(By.CSS_SELECTOR, ".status, [class*='status']")
                str_status = status_element.text.strip()
                status_lines = str_status.splitlines()
                property_data['status'] = status_lines[0] if status_lines else str_status
                line2 = status_lines[1] if len(status_lines) > 1 else None
                property_data['days_on_market'] = line2.split()[-1] if line2 else None
            except NoSuchElementException:
                # Default to 'Active' if no status found
                property_data['status'] = 'Active'
            
        except Exception as e:
            print(f"Error extracting property data: {e}")
        
        return property_data
    
    def has_next_page(self):
        try:
            next_button = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.pagination.pagination-lg"))
            )
            li_elements = next_button.find_elements(By.CSS_SELECTOR, "li")
            for li_element in li_elements:
                try:
                    a_element_text = li_element.find_element(By.TAG_NAME, "a").text.strip()
                    if a_element_text and a_element_text.lower() == "next":
                        return True, li_element
                except NoSuchElementException:
                    continue
        except TimeoutException:
            print("❌ Timeout waiting for pagination")
        except Exception as e:
            print(f"❌ Error checking for next page: {e}")
        return False, None

    def scrape_properties(self):
        """Scrape property listings from the current page"""
        properties = []
        next_boolean = self.has_next_page()
        while next_boolean:
            try:
                print("Waiting for property listings to load...")
                
                # Wait for the property cards container - based on your HTML structure
                properties_container = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.property___cards"))
                )
                print("Found properties container")
                
                # Find all property list items with MLS IDs
                property_elements = properties_container.find_elements(By.CSS_SELECTOR, "li[id*='mls-inline-']")
                print(f"Found {len(property_elements)} property elements")
                
                if not property_elements:
                    print("No properties found with expected structure")
                    return properties
                
                # Extract data from each property
                for i, property_element in enumerate(property_elements):
                    print(f"\n--- Processing property {i+1}/{len(property_elements)} ---")
                    # Scroll element into view to ensure it's loaded
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", property_element)
                    time.sleep(1)
                    
                    property_data = self.extract_property_data(property_element)
                    
                    # Only add if we got meaningful data
                    if any([property_data['mls_id'], property_data['price'], property_data['address']]):
                        properties.append(property_data)
                        print(f"✅ Added property: MLS {property_data['mls_id']}, Price: {property_data['price']}")
                        print(f"   Address: {property_data['address']}")
                        print(f"   Details: {property_data['beds']} beds, {property_data['baths']} baths, {property_data['sqft']} sqft")
                    else:
                        print(f"❌ Skipped property {i+1} - insufficient data")

                time.sleep(0.5)
                next_boolean, next_button = self.has_next_page()
                if next_boolean:
                    next_button.click()
            except TimeoutException:
                print("❌ Timeout waiting for property listings to load")
            except Exception as e:
                print(f"❌ Error scraping properties: {e}")
            
        return properties
    
    
    def save_to_csv(self, properties, filename=None):
        """Save properties to CSV file"""
        if not properties:
            print("No properties to save")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"utah_properties_{timestamp}.csv"
        
        fieldnames = properties[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(properties)
        
        print(f"💾 Saved {len(properties)} properties to {filename}")
    
    def save_to_json(self, properties, filename=None):
        """Save properties to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"utah_properties_{timestamp}.json"
            
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(properties, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(properties)} properties to {filename}")
    
    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()

def main():
    """Main function to run the scraper"""
    print("🏠 Starting Utah Real Estate Scraper for South Jordan...")
    
    # Set headless=False to see the browser action
    scraper = UtahRealEstateScraper(headless=False)
    
    try:
        # Start the scraper
        scraper.start_driver()
        
        # Navigate to search page
        if scraper.navigate_to_search("South Jordan, UT"):
            print("✅ Successfully navigated to search page")
            
            # Scrape properties
            print("\n🔍 Starting property extraction...")
            properties = scraper.scrape_properties()
            
            if properties:
                print(f"\n🎉 Successfully scraped {len(properties)} properties!")
                
                # Save results
                scraper.save_to_csv(properties)
                scraper.save_to_json(properties)
                
                # Print summary
                print("\n📊 Sample properties:")
                for i, prop in enumerate(properties[:5]):
                    print(f"{i+1}. MLS: {prop['mls_id']}")
                    print(f"   Price: {prop['price']}")
                    print(f"   Address: {prop['address']}")
                    print(f"   Details: {prop['beds']} beds, {prop['baths']} baths, {prop['sqft']} sqft")
                    print()
                    
                # Summary stats
                prices = [p['price'] for p in properties if p['price']]
                print(f"📈 Summary: {len(properties)} total properties, {len(prices)} with prices")
                
            else:
                print("❌ No properties found - check selectors or page structure")
        else:
            print("❌ Failed to navigate to search page")
            
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔒 Closing browser...")
        scraper.close()
        print("✅ Scraper completed")

if __name__ == "__main__":
    main()

