# server.py
from flask import Flask, request, send_from_directory, jsonify, url_for
import os, base64, requests, threading
from together import Together
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static", static_url_path="")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Together client - don't hardcode in production; use env var
TOGETHER_API_KEY = "ba974f79d25bc4a6b6e8b2e1cb47d780df948cfaefd4557faaae7cb2ef493d14"
client = Together(api_key=TOGETHER_API_KEY)

MODEL_NAME = "black-forest-labs/FLUX.1-Kontext-dev"  # or exact model slug on Together
RESULT_FILENAME = "result.jpg"
lock = threading.Lock()  # avoid concurrent requests overwriting each other

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/current", methods=["GET"])
def current():
    """Return URL of current result if exists."""
    result_path = os.path.join(UPLOAD_FOLDER, RESULT_FILENAME)
    if os.path.exists(result_path):
        return jsonify({"current": url_for("serve_upload", filename=RESULT_FILENAME, _external=True)})
    return jsonify({"current": None})

@app.route("/upload", methods=["POST"])
def upload():
    """
    Accepts form-data:
      - image (file) [optional]
      - prompt (string) [required]
      - use_last (string "true" / "false") [optional]
    If use_last == "true" (or no file provided), server uses the last result.jpg as the base image.
    If a new file is provided and use_last != "true", the new file becomes the base.
    """
    use_last = request.form.get("use_last", "false").lower() == "true"
    prompt = request.form.get("prompt", "").strip()
    file = request.files.get("image")

    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    # Decide base image path
    if (file and file.filename and not use_last):
        filename = secure_filename(file.filename)
        base_image_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(base_image_path)
    else:
        # Use last result
        result_path = os.path.join(UPLOAD_FOLDER, RESULT_FILENAME)
        if os.path.exists(result_path):
            base_image_path = result_path
        else:
            return jsonify({"error": "No previous result available. Please upload an image first."}), 400

    # Read base image and encode
    with open(base_image_path, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    # Call Together API inside a lock to avoid overlapping edits
    try:
        with lock:
            response = client.images.generate(
                prompt=prompt,
                model=MODEL_NAME,
                condition_image=img_b64,
                size="512x512"  # adjust if you want match_input_image or different res
            )

        # Debug print (server console)
        print("Together API response:", response)

        if not response or not getattr(response, "data", None):
            return jsonify({"error": "No result returned from Together API"}), 502

        # The Together response may provide a URL; download it
        image_url = response.data[0].url
        img_resp = requests.get(image_url, timeout=30)
        if img_resp.status_code != 200:
            return jsonify({"error": "Failed to download image from Together", "api_url": image_url}), 502

        # Save as result.jpg (overwrite)
        output_path = os.path.join(UPLOAD_FOLDER, RESULT_FILENAME)
        with open(output_path, "wb") as out:
            out.write(img_resp.content)

        # Return the publicly-accessible URL to client (with cache bust param)
        result_url = url_for("serve_upload", filename=RESULT_FILENAME, _external=True)
        return jsonify({"result": result_url})

    except Exception as e:
        # Return the error message (useful for debugging; in production, sanitize)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
