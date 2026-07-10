from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import db
from models import IndustryProfile, WorkforceDemand, Certificate, ParticipantProfile
from werkzeug.security import generate_password_hash, check_password_hash

industry = Blueprint('industry', __name__)

def industry_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'industry':
            flash('Industry access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@industry.route('/dashboard')
@login_required
@industry_required
def dashboard():
    profile       = IndustryProfile.query.filter_by(user_id=current_user.id).first()
    my_demands    = WorkforceDemand.query.filter_by(user_id=current_user.id).order_by(WorkforceDemand.submitted_at.desc()).all()
    total_demands = len(my_demands)
    fulfilled     = sum(1 for d in my_demands if d.status == 'fulfilled')
    pending       = sum(1 for d in my_demands if d.status == 'pending')
    not_available = sum(1 for d in my_demands if d.status == 'not_available')
    return render_template('industry/dashboard.html',
        profile       = profile,
        my_demands    = my_demands[:5],
        total_demands = total_demands,
        fulfilled     = fulfilled,
        pending       = pending,
        not_available = not_available
    )

# ── WORKFORCE DATABASE ────────────────────────────────────────────────────────
@industry.route('/workforce')
@login_required
@industry_required
def workforce():
    skill_filter  = request.args.get('skill', '')
    city_filter   = request.args.get('city', '')
    status_filter = request.args.get('status', '')
    sort_by       = request.args.get('sort_by', 'name')

    query = Certificate.query.join(
        ParticipantProfile,
        Certificate.participant_id == ParticipantProfile.id
    )

    if skill_filter:
        query = query.filter(Certificate.skill_certified.ilike(f'%{skill_filter}%'))
    if city_filter:
        query = query.filter(ParticipantProfile.city.ilike(f'%{city_filter}%'))
    if status_filter:
        query = query.filter(ParticipantProfile.working_status == status_filter)

    if sort_by == 'name':
        query = query.order_by(ParticipantProfile.full_name.asc())
    elif sort_by == 'skill':
        query = query.order_by(Certificate.skill_certified.asc())
    elif sort_by == 'city':
        query = query.order_by(ParticipantProfile.city.asc())
    elif sort_by == 'date':
        query = query.order_by(Certificate.issued_date.desc())
    elif sort_by == 'status':
        query = query.order_by(ParticipantProfile.working_status.asc())

    certificates = query.all()

    return render_template('industry/workforce.html',
        certificates  = certificates,
        skill_filter  = skill_filter,
        city_filter   = city_filter,
        status_filter = status_filter,
        sort_by       = sort_by
    )

# ── VIEW WORKER PROFILE ───────────────────────────────────────────────────────
@industry.route('/workforce/worker/<int:participant_id>')
@login_required
@industry_required
def view_worker(participant_id):
    profile = ParticipantProfile.query.get_or_404(participant_id)
    certs   = Certificate.query.filter_by(participant_id=participant_id).all()
    return render_template('industry/view_worker.html',
        profile = profile,
        certs   = certs
    )

# ── SUBMIT DEMAND ─────────────────────────────────────────────────────────────
@industry.route('/demand', methods=['GET', 'POST'])
@login_required
@industry_required
def submit_demand():
    if request.method == 'POST':
        skill_required   = request.form.get('skill_required')
        quantity         = int(request.form.get('quantity'))
        description      = request.form.get('description')
        job_position     = request.form.get('job_position')
        machines_used    = request.form.get('machines_used')
        experience_level = request.form.get('experience_level')
        min_education    = request.form.get('min_education')
        work_location    = request.form.get('work_location')
        urgency_level    = request.form.get('urgency_level')

        matches = Certificate.query.filter(
            Certificate.skill_certified.ilike(f'%{skill_required}%')
        ).count()
        status = 'fulfilled' if matches >= quantity else \
                 'not_available' if matches == 0 else 'pending'

        demand = WorkforceDemand(
            user_id          = current_user.id,
            skill_required   = skill_required,
            quantity         = quantity,
            description      = description,
            job_position     = job_position,
            machines_used    = machines_used,
            experience_level = experience_level,
            min_education    = min_education,
            work_location    = work_location,
            urgency_level    = urgency_level,
            status           = status
        )
        db.session.add(demand)
        db.session.commit()

        if matches >= quantity:
            flash(f'Great news! {matches} certified workers found!', 'success')
        elif matches > 0:
            flash(f'Partially available: {matches} found, you need {quantity}.', 'warning')
        else:
            flash('No certified workforce available yet. Request recorded.', 'warning')

        return redirect(url_for('industry.workforce') + f'?skill={skill_required}')
    return render_template('industry/demand.html')

# ── MY DEMANDS ────────────────────────────────────────────────────────────────
@industry.route('/my-demands')
@login_required
@industry_required
def my_demands():
    demands = WorkforceDemand.query.filter_by(user_id=current_user.id).order_by(WorkforceDemand.submitted_at.desc()).all()
    return render_template('industry/my_demands.html', demands=demands)

# ── EDIT PROFILE ──────────────────────────────────────────────────────────────
@industry.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@industry_required
def edit_profile():
    profile = IndustryProfile.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        profile.industry_name  = request.form.get('industry_name')
        profile.sector         = request.form.get('sector')
        profile.address        = request.form.get('address')
        profile.contact_number = request.form.get('contact_number')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('industry.dashboard'))
    return render_template('industry/edit_profile.html', profile=profile)

# ── CHANGE PASSWORD ───────────────────────────────────────────────────────────
@industry.route('/change-password', methods=['GET', 'POST'])
@login_required
@industry_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw     = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')
        from werkzeug.security import check_password_hash, generate_password_hash
        if not check_password_hash(current_user.password, current_pw):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('industry.change_password'))
        if new_pw != confirm_pw:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('industry.change_password'))
        current_user.password = generate_password_hash(new_pw)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('industry.dashboard'))
    return render_template('industry/change_password.html')