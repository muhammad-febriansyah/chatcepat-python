from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv
from scraper import GoogleMapsScraper
from google_places_scraper import GooglePlacesAPIScraper, test_api_key

load_dotenv()

app = Flask(__name__)
CORS(app, origins=[os.getenv('ALLOWED_ORIGIN', 'http://localhost:8000')])

# Configuration
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    print("FATAL: API_KEY is not set. Configure it in .env", file=sys.stderr)
    sys.exit(1)

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
SCRAPER_MODE = os.getenv('SCRAPER_MODE', 'api').lower()  # 'api' or 'selenium'


def verify_api_key():
    """Verify API key from request header"""
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != API_KEY:
        return False
    return True


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if not verify_api_key():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    google_api_status = 'not_configured'
    if GOOGLE_MAPS_API_KEY and SCRAPER_MODE == 'api':
        google_api_status = 'configured'

    return jsonify({
        'status': 'ok',
        'message': 'Google Maps Scraper API is running',
        'scraper_mode': SCRAPER_MODE,
        'google_api_status': google_api_status
    })


@app.route('/api/scrape', methods=['POST'])
def scrape():
    """
    Endpoint untuk scraping Google Maps

    Request Body:
    {
        "keyword": "restaurant",
        "location": "Jakarta",
        "kecamatan": "Menteng",
        "max_results": 20
    }

    Headers:
    X-API-Key: your-secret-api-key
    """
    # Verify API key
    if not verify_api_key():
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized: Invalid API key'
        }), 401

    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['keyword', 'location', 'kecamatan']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400

        keyword = data['keyword']
        location = data['location']
        kecamatan = data['kecamatan']
        max_results = data.get('max_results', 20)

        # Validate max_results
        max_limit = 60 if SCRAPER_MODE == 'api' else 100
        if max_results < 1 or max_results > max_limit:
            return jsonify({
                'status': 'error',
                'message': f'max_results must be between 1 and {max_limit}'
            }), 400

        # Choose scraper based on mode
        if SCRAPER_MODE == 'api':
            # Use Google Places API
            if not GOOGLE_MAPS_API_KEY:
                return jsonify({
                    'status': 'error',
                    'message': 'Google Maps API key not configured. Set GOOGLE_MAPS_API_KEY in .env'
                }), 500

            scraper = GooglePlacesAPIScraper(GOOGLE_MAPS_API_KEY)
            results = scraper.search_places(keyword, location, kecamatan, max_results)

            return jsonify({
                'status': 'success',
                'data': results,
                'total': len(results),
                'method': 'google_places_api',
                'query': {
                    'keyword': keyword,
                    'location': location,
                    'kecamatan': kecamatan,
                    'max_results': max_results
                }
            })

        else:
            # Use Selenium scraping
            scraper = GoogleMapsScraper(
                headless=True,
                use_proxy=os.getenv('USE_PROXY', 'false').lower() == 'true'
            )

            try:
                # Perform scraping
                results = scraper.search_places(keyword, location, kecamatan, max_results)

                return jsonify({
                    'status': 'success',
                    'data': results,
                    'total': len(results),
                    'method': 'selenium_scraping',
                    'query': {
                        'keyword': keyword,
                        'location': location,
                        'kecamatan': kecamatan,
                        'max_results': max_results
                    }
                })

            finally:
                scraper.close_driver()

    except Exception as e:
        print(f"Scraping error: {str(e)}", file=sys.stderr)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during scraping'
        }), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'

    print(f"Starting Google Maps Scraper API on port {port}")
    print(f"Debug mode: {debug}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
