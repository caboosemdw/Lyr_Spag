from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
import requests
import os
from config import DevelopmentConfig, ProductionConfig
import secrets
import click
from flask.cli import with_appcontext
from extensions import db

app = Flask(__name__)

# Load config dynamically (production on Heroku, dev locally)
if os.getenv("FLASK_ENV") == "production":
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

# Initialize db with app
db.init_app(app)

# Import models after db is initialized
from models import Member, SyncStatus

# Custom Jinja filter to format numbers with commas
@app.template_filter("format_number")
def format_number(value):
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value

# CLI command to generate a new SECRET_KEY
@app.cli.command("generate-key")
@with_appcontext
def generate_key():
    """Generate a new SECRET_KEY for Flask sessions/CSRF."""
    key = secrets.token_hex(32)
    click.echo(f"Your new SECRET_KEY:\n{key}")
    click.echo("\n➡ Add this to your .env file as:\nSECRET_KEY=" + key)

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

    sync_status = SyncStatus.query.first()
    member_data = []
    last_updated_str = None
    updated_from = None

    if sync_status and sync_status.last_sync > datetime.utcnow() - timedelta(minutes=5):
        # ✅ Use DB only
        members = Member.query.all()
        member_data = [[m.username, m.id, m.area, m.level, m.base_stats] for m in members]

        delta = datetime.utcnow() - sync_status.last_sync
        minutes, seconds = divmod(int(delta.total_seconds()), 60)
        last_updated_str = f"{minutes}m {seconds}s ago"
        updated_from = "DB"
    else:
        # 🔄 Fetch from API
        api_url = app.config["API_URL"]
        if api_url and api_url != "No API URL Found":
            try:
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                guild_data = response.json()
                members = guild_data.get("members", [])
                for m in members:
                    member = Member.query.get(m["id"])
                    if not member:
                        member = Member(id=m["id"], username=m["username"])

                    member.username = m.get("username", "N/A")
                    member.area = m.get("area")
                    member.level = m.get("level")
                    member.base_stats = m.get("base_stats")

                    db.session.add(member)

                    member_data.append([
                        member.username,
                        member.id,
                        member.area,
                        member.level,
                        member.base_stats
                    ])

                # Update sync time
                if not sync_status:
                    sync_status = SyncStatus(last_sync=datetime.utcnow())
                    db.session.add(sync_status)
                else:
                    sync_status.last_sync = datetime.utcnow()

                db.session.commit()

                # ✅ API refresh
                last_updated_str = "just now"
                updated_from = "API"

            except requests.exceptions.RequestException as e:
                member_data = [["Error", str(e), "-", "-", "-"]]

    return render_template(
        "memberdata.html",
        title="Spag Member Data",
        founded="14-Jan-2023",
        age_days=age_days,
        member_data=member_data,
        last_updated_str=last_updated_str,
        updated_from=updated_from
    )

@app.route("/gbosscalc", methods=["GET"])
def gbosscalc():
    members = Member.query.all()
    return render_template(
        "gbosscalc.html",
        title="Spag GBoss Calc",
        members=members
    )

@app.route("/update_gboss", methods=["POST"])
def update_gboss():
    members = Member.query.all()
    for member in members:
        dmg = request.form.get(f"gboss_dmg_{member.id}")
        override = request.form.get(f"gboss_dmg_override_{member.id}")
        catzord = request.form.get(f"gboss_catzord_{member.id}")

        if dmg is not None:
            member.gboss_dmg = int(dmg) if dmg else None

        if override is not None:
            if override.strip() == "":
                pass  # no change
            elif override.strip() == "0":
                member.gboss_dmg_override = None
            else:
                member.gboss_dmg_override = int(override)

        if catzord is not None:
            member.gboss_catzord = True if catzord == "on" else False

        db.session.add(member)

    db.session.commit()
    return "OK"

if __name__ == "__main__":
    app.run(debug=True)
