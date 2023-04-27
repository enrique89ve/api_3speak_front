

from flask import Flask, jsonify, request
from flask_caching import Cache
import requests
from bs4 import BeautifulSoup
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from flask_cors import CORS



app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1 per 1 second", "100 per 1 second"],
    storage_uri="memory://",
)


CORS(app)

logging.getLogger('flask_cors').level = logging.DEBUG


cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_KEY_PREFIX': '3Speakviews'})





@cache.memoize(timeout=60)
def get_3speak_views(video_id):
    url = f'https://3speak.tv/watch?v={video_id}'
    for i in range(3):
        try:
            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')
            result = soup.find('span', class_="mr-1")
            if result:
                views = result.text.strip()
                views = views.replace('<i class="fas fa-eye"></i>', '').strip()
                return int(views)
        except Exception as e:
            print("Error fetching views:", e)
    return None
    

@app.route('/')
def api_info():
    return '''<h1>3Speak Views API</h1>
    <p>This API returns the number of views for a given 3Speak video.</p>
    <p>To use the API, make a GET request to /views/{video_id}, where {video_id} is the ID of the video on 3Speak (e.g. "sagarkothari88/puorgnrlmg").</p>
    <p>For example: /views?id=sagarkothari88/puorgnrlmg</p>
    '''

@app.route('/views', methods=['GET'])
@limiter.limit("10/second", override_defaults=False)
def get_views():
    video_id = request.args.get('id', type=str)
    if not video_id:
        return jsonify({"error": "The video ID is required."}), 400

    url = video_id
    url = str(url)
    views = get_3speak_views(url)
    if views is None:
        return jsonify({"error": "Could not fetch the number of views."}), 500

    return jsonify({"views": views})

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found."}), 404

# Maneja excepciones generales
@app.errorhandler(Exception)
def handle_exception(e):
    print("Unhandled exception:", e)
    return jsonify({"error": "Internal server error."}), 500



if __name__ == '__main__':
    app.run(debug=False)
