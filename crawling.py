import sys
import json
import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class GoogleMapsScraper:
    def __init__(self, headless: bool = True):
        """Initialize the scraper with Chrome options"""
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        self.driver = None

    def start_driver(self):
        """Start the Chrome driver"""
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)

    def close_driver(self):
        """Close the Chrome driver"""
        if self.driver:
            self.driver.quit()

    def search_places(self, keyword: str, location: str, kecamatan: str, max_results: int = 20) -> List[Dict]:
        """
        Search for places on Google Maps

        Args:
            keyword: Search keyword (e.g., 'restaurant', 'hotel')
            location: City/Area name (e.g., 'Jakarta')
            kecamatan: District/Kecamatan name
            max_results: Maximum number of results to scrape

        Returns:
            List of dictionaries containing place information
        """
        if not self.driver:
            self.start_driver()

        query = f"{keyword} di {kecamatan}, {location}"
        search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

        print(f"Searching: {query}", file=sys.stderr)
        self.driver.get(search_url)

        # Wait for results to load
        time.sleep(5)

        results = []
        scrollable_div = None

        try:
            # Find the scrollable results container
            scrollable_div = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')

            last_height = 0
            scroll_attempts = 0
            max_scroll_attempts = 10

            while len(results) < max_results and scroll_attempts < max_scroll_attempts:
                # Scroll the results panel
                self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                time.sleep(2)

                # Get all place elements
                place_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div > a')

                # Check if we've reached the end
                new_height = self.driver.execute_script('return arguments[0].scrollHeight', scrollable_div)
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0

                last_height = new_height

                # Extract data from visible elements
                for idx, element in enumerate(place_elements):
                    if len(results) >= max_results:
                        break

                    try:
                        # Get the place URL
                        place_url = element.get_attribute('href')

                        # Skip if already processed
                        if any(r.get('url') == place_url for r in results):
                            continue

                        # Click to get details
                        self.driver.execute_script("arguments[0].click();", element)
                        time.sleep(2)

                        # Extract place data
                        place_data = self._extract_place_data(kecamatan, location)
                        if place_data:
                            place_data['url'] = place_url
                            results.append(place_data)
                            print(f"Scraped: {place_data.get('name', 'Unknown')} ({len(results)}/{max_results})", file=sys.stderr)

                    except Exception as e:
                        print(f"Error extracting place {idx}: {str(e)}", file=sys.stderr)
                        continue

        except Exception as e:
            print(f"Error during scraping: {str(e)}", file=sys.stderr)

        return results

    def _extract_place_data(self, kecamatan: str, location: str) -> Optional[Dict]:
        """Extract data from a place detail page"""
        try:
            place_data = {
                'kecamatan': kecamatan,
                'location': location,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # Get place name
            try:
                name_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.DUwDvf'))
                )
                place_data['name'] = name_element.text
            except:
                place_data['name'] = None

            # Get rating
            try:
                rating_element = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice > span[role="img"]')
                rating_text = rating_element.get_attribute('aria-label')
                if rating_text:
                    # Extract rating number (e.g., "4.5 stars" -> 4.5)
                    place_data['rating'] = rating_text.split()[0]
                else:
                    place_data['rating'] = None
            except:
                place_data['rating'] = None

            # Get review count
            try:
                reviews_element = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice > span:nth-child(2) > span > span')
                reviews_text = reviews_element.get_attribute('aria-label')
                if reviews_text:
                    # Extract number from text like "1,234 reviews"
                    place_data['review_count'] = reviews_text.split()[0].replace(',', '')
                else:
                    place_data['review_count'] = None
            except:
                place_data['review_count'] = None

            # Get address
            try:
                address_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]')
                address_text = address_button.get_attribute('aria-label')
                if address_text and 'Address:' in address_text:
                    place_data['address'] = address_text.replace('Address:', '').strip()
                else:
                    place_data['address'] = None
            except:
                place_data['address'] = None

            # Get phone
            try:
                phone_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id^="phone"]')
                phone_text = phone_button.get_attribute('aria-label')
                if phone_text and 'Phone:' in phone_text:
                    place_data['phone'] = phone_text.replace('Phone:', '').strip()
                else:
                    place_data['phone'] = None
            except:
                place_data['phone'] = None

            # Get website
            try:
                website_link = self.driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
                place_data['website'] = website_link.get_attribute('href')
            except:
                place_data['website'] = None

            # Get category
            try:
                category_button = self.driver.find_element(By.CSS_SELECTOR, 'button.DkEaL')
                place_data['category'] = category_button.text
            except:
                place_data['category'] = None

            return place_data if place_data.get('name') else None

        except Exception as e:
            print(f"Error extracting place data: {str(e)}", file=sys.stderr)
            return None


def main():
    """Main function to run scraper from command line"""
    if len(sys.argv) < 4:
        print(json.dumps({
            'status': 'error',
            'message': 'Usage: python crawling.py <keyword> <location> <kecamatan> [max_results]'
        }))
        sys.exit(1)

    keyword = sys.argv[1]
    location = sys.argv[2]
    kecamatan = sys.argv[3]
    max_results = int(sys.argv[4]) if len(sys.argv) > 4 else 20

    scraper = GoogleMapsScraper(headless=True)

    try:
        results = scraper.search_places(keyword, location, kecamatan, max_results)

        output = {
            'status': 'success',
            'data': results,
            'total': len(results),
            'query': {
                'keyword': keyword,
                'location': location,
                'kecamatan': kecamatan,
                'max_results': max_results
            }
        }

        print(json.dumps(output, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({
            'status': 'error',
            'message': str(e)
        }))
        sys.exit(1)

    finally:
        scraper.close_driver()


if __name__ == '__main__':
    main()
