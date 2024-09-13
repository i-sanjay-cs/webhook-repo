import os
from flask import Flask, request, jsonify
import pymongo
from datetime import datetime, timezone

app = Flask(__name__)

mongo_password = os.getenv("MONGO_PASSWORD")

client = pymongo.MongoClient(f"mongodb+srv://toontown8268703019:{mongo_password}@web-hook.6y5og.mongodb.net/webhooks?retryWrites=true&w=majority")
db = client["webhooks"]
collection = db["events"]
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/api/events", methods=["GET"])
def get_events():
    events = collection.find().sort("timestamp", -1).limit(10)
    event_list = []
    
    for event in events:
        event_list.append({
            "author": event["author"],
            "action": event["action"],
            "from_branch": event.get("from_branch", "N/A"),
            "to_branch": event["to_branch"],
            "timestamp": event["timestamp"]
        })
    
    return jsonify(event_list)


@app.route("/webhook", methods=["POST"])
def github_webhook():
    if request.method == "POST":
        data = request.json
        event_type = request.headers.get('X-GitHub-Event')

        event = {
            "request_id": data['after'] if event_type == "push" else data.get('pull_request', {}).get('id', 'unknown'),
            "author": data['pusher']['name'] if event_type == "push" else data.get('pull_request', {}).get('user', {}).get('login', 'unknown'),
            "action": event_type,
            "from_branch": data.get('pull_request', {}).get('head', {}).get('ref', 'unknown') if event_type == "pull_request" else 'N/A',
            "to_branch": data.get('ref', 'N/A') if event_type == "push" else data.get('pull_request', {}).get('base', {}).get('ref', 'unknown'),
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }
        collection.insert_one(event)
        return jsonify({"status": "success", "message": f"Received {event_type} event"}), 200

if __name__ == "__main__":
    app.run(debug=True)
