from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os
from typing import Optional, Dict, Any

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get('PORT', 4000))

def validate_input(body: Dict[str, str]) -> Optional[str]:
    reaction = body.get('reaction')
    cookie = body.get('cookie')
    link = body.get('link')

    if not reaction:
        return "Reaction is required"
    if not cookie:
        return "Facebook cookie is required"
    if not link:
        return "Link is required"
    
    valid_reactions = ['LIKE', 'LOVE', 'CARE', 'HAHA', 'WOW', 'SAD', 'ANGRY']
    if reaction.upper() not in valid_reactions:
        return "Invalid reaction type"
    
    return None

def fetch_metadata(url: str) -> Optional[Dict[str, Any]]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        og_image = (
            soup.find('meta', property='og:image')
            or soup.find('meta', attrs={'name': 'twitter:image'})
        )
        og_title = (
            soup.find('meta', property='og:title')
            or soup.find('title')
            or soup.find('h1')
        )
        og_description = (
            soup.find('meta', property='og:description')
            or soup.find('meta', attrs={'name': 'description'})
            or soup.find('p')
        )
        
        post_content = (
            soup.find(class_='_5pbx')
            or soup.find(class_='userContent')
        )
        
        return {
            'title': og_title.get('content', og_title.text) if og_title else "No title available",
            'description': og_description.get('content', og_description.text) if og_description else "No description available",
            'image': og_image.get('content') if og_image else None,
            'postContent': post_content.text[:300].strip() if post_content else ""
        }
    except Exception as e:
        print(f"Failed to fetch metadata for {url}: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview():
    data = request.get_json()
    link = data.get('link')
    
    try:
        metadata = fetch_metadata(link)
        if not metadata:
            return jsonify({
                'error': "Unable to extract metadata from the provided link."
            }), 404
        
        return jsonify(metadata)
    except Exception as e:
        print(f'Error in preview route: {str(e)}')
        return jsonify({
            'error': "An unexpected error occurred while processing the link.",
            'details': str(e)
        }), 500

@app.route('/react', methods=['POST'])
def react():
    data = request.get_json()
    
    validation_error = validate_input(data)
    if validation_error:
        return jsonify({'error': validation_error}), 400
    
    url = "https://fbpython.click/android_get_react"
    payload = {
        'reaction': data['reaction'].upper(),
        'cookie': data['cookie'],
        'link': data['link'],
        'version': "5.2.1"
    }
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "okhttp/3.9.1"
    }
    
    try:
        print(f"Sending request to {url} with payload:", {
            **payload,
            'cookie': '[REDACTED]' if payload['cookie'] else 'N/A'
        })
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        
        print("Received response:", response.json())
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {str(e)}")
        
        if hasattr(e, 'response'):
            return jsonify({
                'error': e.response.json(),
                'statusCode': e.response.status_code
            }), e.response.status_code
        
        return jsonify({
            'error': "An unexpected error occurred.",
            'details': str(e)
        }), 500

if __name__ == '__main__':
    print(f"Server is running on http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
