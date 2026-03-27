from flask import Flask, request, send_file, jsonify
from pathlib import Path
import tempfile

from radar import generate_forecast_radar

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/generate-chart", methods=["POST"])
def generate_chart():
    data = request.get_json()

    try:
        scores = [
            int(data["succession"]),
            int(data["language"]),
            int(data["coaching"]),
            int(data["conflict"]),
            int(data["assessments"]),
        ]
    except Exception:
        return jsonify({"error": "Missing or invalid score fields"}), 400

    temp_dir = Path(tempfile.mkdtemp())
    svg_path = temp_dir / "forecast_radar.svg"
    png_path = temp_dir / "forecast_radar.png"

    generate_forecast_radar(
        scores=scores,
        output_svg=str(svg_path),
        output_png=str(png_path),
    )

    return send_file(
        str(png_path),
        mimetype="image/png"
    )
