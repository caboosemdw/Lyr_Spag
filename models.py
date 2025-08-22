from datetime import datetime
from extensions import db

class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    area = db.Column(db.Integer, nullable=True)
    level = db.Column(db.Integer, nullable=True)
    base_stats = db.Column(db.Integer, nullable=True)

    # Guild boss damage values (now Integer, consistent with GBossRun)
    gboss_dmg = db.Column(db.Integer, nullable=True)
    gboss_dmg_override = db.Column(db.Integer, nullable=True)

    # Boolean: does the member have Catzord equipped?
    gboss_catzord = db.Column(db.Boolean, default=False, nullable=False)

    # Track when this record was last updated
    last_updated = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ✅ Relationship to gboss_runs
    runs = db.relationship("GBossRun", back_populates="member", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Member {self.username}>"


class GBossRun(db.Model):
    __tablename__ = "gboss_runs"

    id = db.Column(db.Integer, primary_key=True)  # auto increment PK
    boss_id = db.Column(db.Integer, nullable=False)  # Which boss was fought
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)  # FK to Member
    damage = db.Column(db.Integer, nullable=False)  # Damage dealt
    rp = db.Column(db.Integer, nullable=False)  # Reward points or similar metric

    # ✅ Relationship back to member
    member = db.relationship("Member", back_populates="runs")

    def __repr__(self):
        return f"<GBossRun boss={self.boss_id} member={self.member_id} dmg={self.damage} rp={self.rp}>"


class SyncStatus(db.Model):
    __tablename__ = "sync_status"

    id = db.Column(db.Integer, primary_key=True)
    last_sync = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SyncStatus last_sync={self.last_sync}>"
