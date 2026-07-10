from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, IndustryProfile, ParticipantProfile
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        user     = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))
        if not user.is_approved and user.role != 'participant':
            flash('Your account is pending approval by admin.', 'warning')
            return redirect(url_for('auth.login'))
        login_user(user)
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'industry':
            return redirect(url_for('industry.dashboard'))
        else:
            return redirect(url_for('participant.dashboard'))
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email            = request.form.get('email')
        password         = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role             = request.form.get('role')

        if not role:
            flash('Please select a role.', 'danger')
            return redirect(url_for('auth.register'))
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            email       = email,
            password    = hashed_password,
            role        = role,
            is_approved = True if role == 'participant' else False
        )
        db.session.add(new_user)
        db.session.flush()

        if role == 'industry':
            profile = IndustryProfile(
                user_id        = new_user.id,
                industry_name  = request.form.get('industry_name'),
                sector         = request.form.get('sector'),
                address        = request.form.get('industry_address'),
                contact_number = request.form.get('contact_number')
            )
            db.session.add(profile)
        elif role == 'participant':
            dob_str = request.form.get('date_of_birth')
            dob     = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
            profile = ParticipantProfile(
                user_id        = new_user.id,
                full_name      = request.form.get('full_name'),
                gender         = request.form.get('gender'),
                place_of_birth = request.form.get('place_of_birth'),
                date_of_birth  = dob,
                address        = request.form.get('participant_address'),
                phone_number   = request.form.get('phone_number'),
                education      = request.form.get('education')
            )
            db.session.add(profile)

        db.session.commit()

        if role == 'industry':
            flash('Account created! Please wait for admin approval.', 'success')
        else:
            flash('Account created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))