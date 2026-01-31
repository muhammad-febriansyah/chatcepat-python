import os
import sys
import time
import requests
from typing import List, Dict, Optional


class GooglePlacesAPIScraper:
    """
    Scraper menggunakan Google Places API (Official)

    Keuntungan:
    - Tidak akan di-block
    - Data lebih akurat dan lengkap
    - Lebih cepat (tidak perlu render browser)
    - Legal dan sesuai TOS Google

    Kekurangan:
    - Berbayar (tapi ada free tier $200/bulan)
    - Perlu API key
    """

    def __init__(self, api_key: str):
        """Initialize scraper with Google Maps API key"""
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"

    def search_places(self, keyword: str, location: str, kecamatan: str, max_results: int = 20) -> List[Dict]:
        """
        Search for places using Google Places API

        Args:
            keyword: Search keyword (e.g., 'restaurant', 'hotel')
            location: City/Area name (e.g., 'Jakarta')
            kecamatan: District/Kecamatan name
            max_results: Maximum number of results (max 60 per request due to API limit)

        Returns:
            List of dictionaries containing place information
        """
        query = f"{keyword} di {kecamatan}, {location}"
        print(f"Searching with Google Places API: {query}", file=sys.stderr)

        results = []
        next_page_token = None

        # Google Places API returns max 20 results per page, max 3 pages (60 total)
        max_results = min(max_results, 60)

        while len(results) < max_results:
            # Text Search API
            params = {
                'query': query,
                'key': self.api_key,
                'language': 'id',
            }

            if next_page_token:
                params['pagetoken'] = next_page_token

            try:
                response = requests.get(
                    f"{self.base_url}/textsearch/json",
                    params=params,
                    timeout=30
                )

                data = response.json()

                if data.get('status') != 'OK' and data.get('status') != 'ZERO_RESULTS':
                    error_msg = data.get('error_message', data.get('status'))
                    print(f"API Error: {error_msg}", file=sys.stderr)
                    break

                places = data.get('results', [])

                if not places:
                    break

                # Process each place
                for place in places:
                    if len(results) >= max_results:
                        break

                    # Pass keyword as category
                    place_data = self._extract_place_data(place, kecamatan, location, keyword)
                    if place_data:
                        results.append(place_data)
                        print(f"Scraped: {place_data.get('name', 'Unknown')} ({len(results)}/{max_results})", file=sys.stderr)

                # Check for next page
                next_page_token = data.get('next_page_token')

                if not next_page_token or len(results) >= max_results:
                    break

                # Required delay before requesting next page (Google API requirement)
                time.sleep(2)

            except Exception as e:
                print(f"Error during API request: {str(e)}", file=sys.stderr)
                break

        return results

    def _extract_place_data(self, place: Dict, kecamatan: str, location: str, keyword: str = None) -> Optional[Dict]:
        """Extract data from Google Places API response"""
        try:
            place_id = place.get('place_id')

            # Get detailed information using Place Details API
            details = self._get_place_details(place_id)

            # Use the searched keyword as category, fallback to Google types
            category = keyword if keyword else (', '.join(place.get('types', [])[:2]) if place.get('types') else None)

            place_data = {
                'name': place.get('name'),
                'kecamatan': kecamatan,
                'location': location,
                'category': category,
                'rating': place.get('rating'),
                'review_count': place.get('user_ratings_total'),
                'address': place.get('formatted_address'),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # Add details from Place Details API
            if details:
                place_data['phone'] = details.get('formatted_phone_number')
                place_data['website'] = details.get('website')
                place_data['url'] = details.get('url')

                # Use international phone number if available
                if not place_data['phone'] and details.get('international_phone_number'):
                    place_data['phone'] = details.get('international_phone_number')

            # If no place_id details, use basic info
            if not place_data.get('url'):
                # Create Google Maps URL from coordinates
                lat = place.get('geometry', {}).get('location', {}).get('lat')
                lng = place.get('geometry', {}).get('location', {}).get('lng')
                if lat and lng:
                    place_data['url'] = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

            return place_data if place_data.get('name') else None

        except Exception as e:
            print(f"Error extracting place data: {str(e)}", file=sys.stderr)
            return None

    def _get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed place information using Place Details API"""
        try:
            params = {
                'place_id': place_id,
                'key': self.api_key,
                'fields': 'formatted_phone_number,international_phone_number,website,url',
                'language': 'id'
            }

            response = requests.get(
                f"{self.base_url}/details/json",
                params=params,
                timeout=30
            )

            data = response.json()

            if data.get('status') == 'OK':
                return data.get('result', {})

            return None

        except Exception as e:
            print(f"Error getting place details: {str(e)}", file=sys.stderr)
            return None


def test_api_key(api_key: str) -> bool:
    """Test if Google Maps API key is valid"""
    try:
        params = {
            'query': 'restaurant',
            'key': api_key,
        }

        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params,
            timeout=10
        )

        data = response.json()

        if data.get('status') == 'REQUEST_DENIED':
            print(f"API Key Error: {data.get('error_message', 'Invalid API key')}", file=sys.stderr)
            return False

        return True

    except Exception as e:
        print(f"Error testing API key: {str(e)}", file=sys.stderr)
        return False


if __name__ == '__main__':
    # Test script
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')

    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY not set in environment", file=sys.stderr)
        sys.exit(1)

    scraper = GooglePlacesAPIScraper(api_key)
    results = scraper.search_places('restaurant', 'Jakarta', 'Menteng', 5)

    print(f"\nFound {len(results)} places:")
    for place in results:
        print(f"- {place['name']} (Rating: {place.get('rating', 'N/A')})")
