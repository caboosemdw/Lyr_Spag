from flask import Flask, render_template, request
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.template_filter("format_number")
def format_number(value):
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value

@app.route("/")
def home():
    founded = datetime(2023, 1, 14, 3, 0, 0)
    now = datetime.now()
    age_days = (now - founded).days

    return render_template(
        "index.html",
        title="Lyrania's Spaghetti & Meatballs Guild Website",
        founded="14-Jan-2023",
        age_days=age_days
    )

@app.route("/memberdata")
def memberdata():
    founded = datetime(2023, 1, 14, 3, 0, 0)
    now = datetime.now()
    age_days = (now - founded).days

    api_url = os.getenv("API_URL", "No API URL Found")
    members = []
    member_data = []

    if api_url and api_url != "No API URL Found":
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            guild_data = response.json()
            members = guild_data.get("members", [])
            for m in members:
                member_data.append([
                    m.get("username", "N/A"),
                    m.get("area", "N/A"),
                    m.get("level", "N/A"),
                    m.get("base_stats", "N/A")
                ])
        except requests.exceptions.RequestException as e:
            member_data = [["Error", str(e), "-", "-"]]

    return render_template(
        "memberdata.html",
        title="Spag Member Data",
        founded="14-Jan-2023",
        age_days=age_days,
        member_data=member_data
    )

@app.route("/gbosscalc")
def gbosscalc():
    return render_template(
        "gbosscalc.html",
        title="Spag GBoss Calc"
    )

if __name__ == "__main__":
    app.run(debug=True)
