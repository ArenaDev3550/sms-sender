from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route("/send-sms", methods=["POST"])
def send_sms():
    data = request.get_json(force=True)
    number = data.get("to")
    message = data.get("message")

    if not number or not message:
        return jsonify({"error": "Campos 'to' e 'message' são obrigatórios"}), 400

    try:
        # Comando Termux API
        cmd = ["termux-sms-send", "-n", str(number), message]
        subprocess.run(cmd, check=True)
        return jsonify({"status": "sent", "to": number, "message": message})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
