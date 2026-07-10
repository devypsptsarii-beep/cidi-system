from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

# Import db from a separate file to avoid circular imports
from extensions import db

# ── USER TABLE ────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id          = db.Column(db.Integer, primary_key=True)
    email       = db.Column(db.String(150), unique=True, nullable=False)
    password    = db.Column(db.String(200), nullable=False)
    role        = db.Column(db.String(20),  nullable=False)
    is_approved   = db.Column(db.Boolean, default=False)
    is_imported   = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    industry_profile    = db.relationship('IndustryProfile',    backref='user', uselist=False)
    participant_profile = db.relationship('ParticipantProfile', backref='user', uselist=False)
    workforce_demands   = db.relationship('WorkforceDemand',    backref='user')


# ── INDUSTRY PROFILE ──────────────────────────────────────────────────────────
class IndustryProfile(db.Model):
    __tablename__  = 'industry_profiles'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    industry_name  = db.Column(db.String(200), nullable=False)
    sector         = db.Column(db.String(100), nullable=False)
    address        = db.Column(db.Text,        nullable=False)
    contact_number = db.Column(db.String(20),  nullable=False)


# ── PARTICIPANT PROFILE ───────────────────────────────────────────────────────
class ParticipantProfile(db.Model):
    __tablename__  = 'participant_profiles'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name      = db.Column(db.String(200), nullable=False)
    gender         = db.Column(db.String(10),  nullable=False)
    place_of_birth = db.Column(db.String(100), nullable=False)
    date_of_birth  = db.Column(db.Date,        nullable=False)
    address        = db.Column(db.Text,        nullable=False)
    phone_number   = db.Column(db.String(20),  nullable=False)
    education        = db.Column(db.String(100), nullable=False)
    city             = db.Column(db.String(100))
    working_status   = db.Column(db.String(20), default='unemployed')
    # working_status = 'employed', 'unemployed'

    @property
    def age(self):
        today = date.today()
        born  = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    registrations = db.relationship('TrainingRegistration', backref='participant')
    certificates  = db.relationship('Certificate',          backref='participant')


# ── TRAINING PROGRAM ──────────────────────────────────────────────────────────
class TrainingProgram(db.Model):
    __tablename__  = 'training_programs'
    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(200), nullable=False)
    description    = db.Column(db.Text)
    skill_category = db.Column(db.String(100), nullable=False)
    start_date     = db.Column(db.Date,        nullable=False)
    end_date       = db.Column(db.Date,        nullable=False)
    capacity       = db.Column(db.Integer,     nullable=False)
    status         = db.Column(db.String(20),  default='open')
    created_at     = db.Column(db.DateTime,    default=datetime.utcnow)

    registrations = db.relationship('TrainingRegistration', backref='program')
    certificates  = db.relationship('Certificate',          backref='program')


# ── TRAINING REGISTRATION ─────────────────────────────────────────────────────
class TrainingRegistration(db.Model):
    __tablename__  = 'training_registrations'
    id             = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant_profiles.id'), nullable=False)
    program_id     = db.Column(db.Integer, db.ForeignKey('training_programs.id'),    nullable=False)
    status         = db.Column(db.String(20), default='pending')
    registered_at  = db.Column(db.DateTime,  default=datetime.utcnow)


# ── DIGITAL CERTIFICATE ───────────────────────────────────────────────────────
class Certificate(db.Model):
    __tablename__   = 'certificates'
    id              = db.Column(db.Integer, primary_key=True)
    participant_id  = db.Column(db.Integer, db.ForeignKey('participant_profiles.id'), nullable=False)
    program_id      = db.Column(db.Integer, db.ForeignKey('training_programs.id'),    nullable=False)
    certificate_no  = db.Column(db.String(100), unique=True, nullable=False)
    issued_date     = db.Column(db.Date,    default=date.today)
    skill_certified = db.Column(db.String(200), nullable=False)


# ── WORKFORCE DEMAND ──────────────────────────────────────────────────────────
class WorkforceDemand(db.Model):
    __tablename__    = 'workforce_demands'
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_required   = db.Column(db.String(200), nullable=False)
    quantity         = db.Column(db.Integer,     nullable=False)
    description      = db.Column(db.Text)
    job_position     = db.Column(db.String(200))
    machines_used    = db.Column(db.Text)
    experience_level = db.Column(db.String(50))
    min_education    = db.Column(db.String(50))
    work_location    = db.Column(db.String(200))
    urgency_level    = db.Column(db.String(50))
    status           = db.Column(db.String(20),  default='pending')
    submitted_at     = db.Column(db.DateTime,    default=datetime.utcnow)