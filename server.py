from flask import Flask, request, send_from_directory, jsonify, url_for
import os, base64
from together import Together
import requests

app = Flask(__name__, static_folder="static", static_url_path="")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Together client
client = Together(api_key="ba974f79d25bc4a6b6e8b2e1cb47d780df948cfaefd4557faaae7cb2ef493d14")

MODEL_NAME = "black-forest-labs/FLUX.1-kontext-dev"

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["image"]
    prompt = request.form.get("prompt")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    with open(filepath, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    try:
        response = client.images.generate(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-Kontext-dev",
            condition_image=img_b64,
            size="512x512"
        )

        print("Together API response:", response)

        if not response or not response.data:
            return jsonify({"error": "No result returned from Together API"})

        # ✅ Use URL from API
        image_url = response.data[0].url
        img_resp = requests.get(image_url)

        if img_resp.status_code != 200:
            return jsonify({"error": "Failed to download image", "api_url": image_url})

        output_path = os.path.join(UPLOAD_FOLDER, "result.jpg")
        with open(output_path, "wb") as out:
            out.write(img_resp.content)

        return jsonify({
            "result": url_for("serve_upload", filename="result.jpg", _external=True)
        })

    except Exception as e:
        return jsonify({"error": str(e)})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
