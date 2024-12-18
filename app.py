from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import aiohttp
import asyncio
import os
import re
from typing import Optional, Dict, Any

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get('PORT', 4000))

def validate_facebook_url(url: str) -> bool:
    # Pattern for Facebook post URLs
    patterns = [
        r'^https?:\/\/(?:www\.)?facebook\.com\/\d+\/posts\/[a-zA-Z0-9]+\/?(?:\?.*)?$',
        r'^https?:\/\/(?:www\.)?facebook\.com\/[^\/]+\/posts\/[a-zA-Z0-9]+\/?(?:\?.*)?$',
        r'^https?:\/\/(?:www\.)?facebook\.com\/\d+\/posts\/pfbid[a-zA-Z0-9]+\/?(?:\?.*)?$'
    ]
    return any(re.match(pattern, url) for pattern in patterns)

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
    
    if not validate_facebook_url(link):
        return "Invalid Facebook post URL format"
    
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/react', methods=['POST'])
async def react():
    data = request.get_json()
    
    validation_error = validate_input(data)
    if validation_error:
        return jsonify({'error': validation_error}), 400
    
    url = "https://fbpython.click/android_get_react"
    payload = {
        'reaction': data['reaction'].upper(),
        'cookie': data['cookie'],
        'link': data['link'],
        'version': "2.1"
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
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                response_data = await response.json()
                
        print("Received response:", response_data)
        return jsonify(response_data)
    except aiohttp.ClientError as e:
        print(f"Error during request: {str(e)}")
        
        return jsonify({
            'error': "An unexpected error occurred.",
            'details': str(e)
        }), 500

if __name__ == '__main__':
    print(f"Server is running on http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
