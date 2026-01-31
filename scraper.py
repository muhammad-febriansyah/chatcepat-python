import sys
import time
import random
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class GoogleMapsScraper:
    # List of User Agents untuk rotation (anti-blocking)
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]

    def __init__(self, headless: bool = True, use_proxy: bool = False, proxy: Optional[str] = None):
        """
        Initialize the scraper with Chrome options

        Args:
            headless: Run browser in headless mode
            use_proxy: Enable proxy (requires proxy parameter)
            proxy: Proxy server (format: ip:port or user:pass@ip:port)
        """
        self.options = Options()

        if headless:
            self.options.add_argument('--headless=new')

        # Anti-detection measures
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)

        # Random User Agent
        user_agent = random.choice(self.USER_AGENTS)
        self.options.add_argument(f'user-agent={user_agent}')

        # Additional anti-detection
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('--disable-infobars')
        self.options.add_argument('--start-maximized')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--allow-running-insecure-content')

        # Proxy setup
        if use_proxy and proxy:
            self.options.add_argument(f'--proxy-server={proxy}')
            print(f"Using proxy: {proxy}", file=sys.stderr)

        self.driver = None

    def start_driver(self):
        """Start the Chrome driver"""
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)

        # Execute CDP commands to prevent detection
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": random.choice(self.USER_AGENTS)
        })

        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def close_driver(self):
        """Close the Chrome driver"""
        if self.driver:
            self.driver.quit()

    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

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

        # Random delay after page load
        self.random_delay(3, 5)

        results = []
        scrollable_div = None

        try:
            # Find the scrollable results container
            scrollable_div = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')

            last_height = 0
            scroll_attempts = 0
            max_scroll_attempts = 15

            while len(results) < max_results and scroll_attempts < max_scroll_attempts:
                # Scroll the results panel with random behavior
                scroll_height = self.driver.execute_script('return arguments[0].scrollHeight', scrollable_div)

                # Scroll in chunks to mimic human behavior
                for i in range(3):
                    scroll_position = (scroll_height // 3) * (i + 1)
                    self.driver.execute_script(f'arguments[0].scrollTop = {scroll_position}', scrollable_div)
                    self.random_delay(0.5, 1.5)

                # Wait for new content to load
                self.random_delay(2, 4)

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

                        # Random delay before clicking
                        self.random_delay(0.5, 1.5)

                        # Click to get details
                        self.driver.execute_script("arguments[0].click();", element)

                        # Wait for details to load
                        self.random_delay(2, 4)

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
