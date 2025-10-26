# web_server.py 
from quart import Quart, request, jsonify, render_template, session
from wellness_manager import WellnessManager
import secrets
from dotenv import load_dotenv

load_dotenv()

app = Quart(__name__)
app.secret_key = secrets.token_hex(16)
manager = WellnessManager()

@app.before_serving
async def startup():
    await manager.initialize()

@app.before_request
def assign_session_id():
    if 'user_id' not in session:
        session['user_id'] = f"local-user-{secrets.token_hex(8)}"

@app.route("/")
async def index():
    return await render_template("index.html")

@app.route("/chat", methods=["POST"])
async def chat():
    data = await request.get_json()
    user_input = data.get("message")
    user_id = session.get('user_id')
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    print(f"\nUser: {user_input}")
    
    # Get response (already includes agent info)
    result = await manager.process_message(user_input, user_id=user_id)
    
    print(f"Agent: {result['agent']}")
    print(f"Response: {result['response'][:100]}...")
    
    return jsonify(result)

@app.route("/health")
async def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(port=5000, debug=True)