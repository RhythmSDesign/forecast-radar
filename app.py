from flask import Flask, request, jsonify
from pathlib import Path
import tempfile
import os
import requests

from radar import generate_forecast_radar

app = Flask(__name__)


def get_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def get_zoho_access_token():
    client_id = get_env("ZOHO_CLIENT_ID")
    client_secret = get_env("ZOHO_CLIENT_SECRET")
    refresh_token = get_env("ZOHO_REFRESH_TOKEN")
    accounts_domain = os.getenv("ZOHO_ACCOUNTS_DOMAIN", "https://accounts.zoho.com").strip()

    token_url = f"{accounts_domain}/oauth/v2/token"
    resp = requests.post(
        token_url,
        data={
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    access_token = data.get("access_token")
    api_domain = data.get("api_domain")

    if not access_token:
        raise RuntimeError(f"Could not get access token: {data}")

    if not api_domain:
        api_domain = os.getenv("ZOHO_API_DOMAIN", "https://www.zohoapis.com").strip()

    return access_token, api_domain


def upload_file_to_zfs(png_path):
    access_token, api_domain = get_zoho_access_token()
    url = f"{api_domain}/crm/v8/files"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    with open(png_path, "rb") as f:
        files = {
            "file": ("forecast_radar.png", f, "image/png")
        }
        resp = requests.post(url, headers=headers, files=files, timeout=60)

    resp.raise_for_status()
    data = resp.json()

    if "data" not in data or not data["data"]:
        raise RuntimeError(f"Unexpected ZFS upload response: {data}")

    details = data["data"][0].get("details", {})
    file_id = details.get("id")

    if not file_id:
        raise RuntimeError(f"No file ID returned from ZFS upload: {data}")

    return file_id


def update_lead_compass_chart(lead_id, file_id):
    access_token, api_domain = get_zoho_access_token()
    url = f"{api_domain}/crm/v8/Leads/{lead_id}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "data": [
            {
                "id": lead_id,
                "Compass_Chart": [
                    {
                        "File_Id__s": file_id
                    }
                ]
            }
        ]
    }

    resp = requests.put(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/generate-and-upload-chart", methods=["POST"])
def generate_and_upload_chart():
    data = request.get_json(silent=True) or {}

    try:
        lead_id = str(data["lead_id"]).strip()
        scores = [
            int(data["succession"]),
            int(data["language"]),
            int(data["coaching"]),
            int(data["conflict"]),
            int(data["assessments"]),
        ]
    except Exception:
        return jsonify(
            {
                "error": "Missing or invalid fields. Required: lead_id, succession, language, coaching, conflict, assessments"
            }
        ), 400

    try:
        temp_dir = Path(tempfile.mkdtemp())
        svg_path = temp_dir / "forecast_radar.svg"
        png_path = temp_dir / "forecast_radar.png"

        generate_forecast_radar(
            scores=scores,
            output_svg=str(svg_path),
            output_png=str(png_path),
        )

        file_id = upload_file_to_zfs(str(png_path))
        update_response = update_lead_compass_chart(lead_id, file_id)

        return jsonify(
            {
                "status": "success",
                "lead_id": lead_id,
                "file_id": file_id,
                "crm_response": update_response,
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
