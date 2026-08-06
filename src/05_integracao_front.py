from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS so the frontend can communicate with the backend regardless of origin/port
CORS(app) 

# ADDED: A simple route to verify the server is running when you visit the root URL
@app.route('/', methods=['GET'])
def home():
    return "LoreWeaver API is running! The frontend should connect to /api/chat."

@app.route('/api/chat', methods=['POST'])
def chat():
    # 1. Receive data from the frontend
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({"error": "No message provided"}), 400

    user_message = data['message']

    # 2. For now, we return a simple echo to verify the connection is working.
    placeholder_response = f"Communication successful! The backend received your message: '{user_message}'"

    # 3. Send the response back to the frontend
    return jsonify({"response": placeholder_response})

if __name__ == '__main__':
    print("Starting LoreWeaver API Server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)