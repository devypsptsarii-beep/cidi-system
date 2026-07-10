from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from flask_login import login_required, current_user
from extensions import db
from models import ParticipantProfile, TrainingProgram, TrainingRegistration, Certificate
from datetime import date
import io

participant = Blueprint('participant', __name__)

def participant_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'participant':
            flash('Participant access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@participant.route('/dashboard')
@login_required
@participant_required
def dashboard():
    profile       = ParticipantProfile.query.filter_by(user_id=current_user.id).first()
    my_regs       = TrainingRegistration.query.filter_by(participant_id=profile.id).all() if profile else []
    my_certs      = Certificate.query.filter_by(participant_id=profile.id).all() if profile else []
    open_programs = TrainingProgram.query.filter_by(status='open').all()
    return render_template('participant/dashboard.html',
        profile       = profile,
        my_regs       = my_regs,
        my_certs      = my_certs,
        open_programs = open_programs
    )

# ── TRAINING PROGRAMS ─────────────────────────────────────────────────────────
@participant.route('/programs')
@login_required
@participant_required
def programs():
    all_programs   = TrainingProgram.query.order_by(TrainingProgram.start_date.asc()).all()
    profile        = ParticipantProfile.query.filter_by(user_id=current_user.id).first()
    registered_ids = []
    if profile:
        registered_ids = [r.program_id for r in TrainingRegistration.query.filter_by(participant_id=profile.id).all()]
    return render_template('participant/programs.html',
        programs       = all_programs,
        registered_ids = registered_ids
    )

# ── REGISTER FOR TRAINING ─────────────────────────────────────────────────────
@participant.route('/programs/register/<int:program_id>')
@login_required
@participant_required
def register_training(program_id):
    profile = ParticipantProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('participant.dashboard'))
    program  = TrainingProgram.query.get_or_404(program_id)
    existing = TrainingRegistration.query.filter_by(
        participant_id=profile.id, program_id=program_id
    ).first()
    if existing:
        flash('You are already registered for this program.', 'warning')
        return redirect(url_for('participant.programs'))
    reg = TrainingRegistration(
        participant_id=profile.id,
        program_id=program_id,
        status='pending'
    )
    db.session.add(reg)
    db.session.commit()
    flash(f'Successfully registered for {program.title}! Waiting for admin approval.', 'success')
    return redirect(url_for('participant.programs'))

# ── TRAINING HISTORY ──────────────────────────────────────────────────────────
@participant.route('/history')
@login_required
@participant_required
def history():
    profile = ParticipantProfile.query.filter_by(user_id=current_user.id).first()
    regs    = TrainingRegistration.query.filter_by(participant_id=profile.id).order_by(
        TrainingRegistration.registered_at.desc()
    ).all() if profile else []
    certs   = Certificate.query.filter_by(participant_id=profile.id).all() if profile else []
    return render_template('participant/history.html',
        profile = profile,
        regs    = regs,
        certs   = certs
    )

# ── MY CERTIFICATES ───────────────────────────────────────────────────────────
@participant.route('/certificates')
@login_required
@participant_required
def certificates():
    profile  = ParticipantProfile.query.filter_by(user_id=current_user.id).first()
    my_certs = Certificate.query.filter_by(participant_id=profile.id).all() if profile else []
    return render_template('participant/certificates.html',
        certificates=my_certs, profile=profile
    )

# ── DOWNLOAD CERTIFICATE ──────────────────────────────────────────────────────
@participant.route('/certificates/download/<int:cert_id>')
@login_required
@participant_required
def download_certificate(cert_id):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas

    profile = ParticipantProfile.query.filter_by(user_id=current_user.id).first()
    cert    = Certificate.query.get_or_404(cert_id)

    if cert.participant_id != profile.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('participant.certificates'))

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    p.setFillColor(colors.HexColor('#1e3a8a'))
    p.rect(0, 0, width, height, fill=True, stroke=False)
    margin = 1.5 * cm
    p.setFillColor(colors.white)
    p.roundRect(margin, margin, width - 2*margin, height - 2*margin, 10, fill=True, stroke=False)
    p.setStrokeColor(colors.HexColor('#f97316'))
    p.setLineWidth(4)
    p.roundRect(margin+10, margin+10, width-2*margin-20, height-2*margin-20, 8, fill=False, stroke=True)
    p.setFillColor(colors.HexColor('#1e3a8a'))
    p.setFont('Helvetica-Bold', 36)
    p.drawCentredString(width/2, height-4*cm, 'CERTIFICATE OF COMPLETION')
    p.setFont('Helvetica', 16)
    p.setFillColor(colors.HexColor('#f97316'))
    p.drawCentredString(width/2, height-5.2*cm, 'Center for Digital Industry 4.0 (CIDI 4.0)')
    p.setStrokeColor(colors.HexColor('#f97316'))
    p.setLineWidth(2)
    p.line(3*cm, height-5.8*cm, width-3*cm, height-5.8*cm)
    p.setFillColor(colors.HexColor('#6b7280'))
    p.setFont('Helvetica', 14)
    p.drawCentredString(width/2, height-7*cm, 'This is to certify that')
    p.setFillColor(colors.HexColor('#111827'))
    p.setFont('Helvetica-Bold', 30)
    p.drawCentredString(width/2, height-8.5*cm, cert.participant.full_name)
    p.setStrokeColor(colors.HexColor('#1e3a8a'))
    p.setLineWidth(1)
    p.line(6*cm, height-9*cm, width-6*cm, height-9*cm)
    p.setFillColor(colors.HexColor('#6b7280'))
    p.setFont('Helvetica', 14)
    p.drawCentredString(width/2, height-10*cm, 'has successfully completed the training program')
    p.setFillColor(colors.HexColor('#1e3a8a'))
    p.setFont('Helvetica-Bold', 18)
    p.drawCentredString(width/2, height-11.2*cm, cert.program.title)
    p.setFillColor(colors.HexColor('#6b7280'))
    p.setFont('Helvetica', 13)
    p.drawCentredString(width/2, height-12.2*cm, f'Skill: {cert.skill_certified}')
    p.setFont('Helvetica', 11)
    p.drawString(3*cm, 3.5*cm, f'Certificate No: {cert.certificate_no}')
    p.drawString(3*cm, 2.8*cm, f'Issued Date: {cert.issued_date.strftime("%d %B %Y")}')
    p.drawRightString(width-3*cm, 3.5*cm, 'CIDI 4.0 System')
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
        download_name=f'Certificate_{cert.certificate_no}.pdf',
        mimetype='application/pdf')

# ── EDIT PROFILE ──────────────────────────────────────────────────────────────
@participant.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@participant_required
def edit_profile():
    profile = ParticipantProfile.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        profile.full_name      = request.form.get('full_name')
        profile.gender         = request.form.get('gender')
        profile.place_of_birth = request.form.get('place_of_birth')
        profile.date_of_birth  = date.fromisoformat(request.form.get('date_of_birth'))
        profile.address        = request.form.get('address')
        profile.phone_number   = request.form.get('phone_number')
        profile.education      = request.form.get('education')
        profile.city           = request.form.get('city')
        profile.working_status = request.form.get('working_status')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('participant.dashboard'))
    return render_template('participant/edit_profile.html', profile=profile)

# ── CHANGE PASSWORD ───────────────────────────────────────────────────────────
@participant.route('/change-password', methods=['GET', 'POST'])
@login_required
@participant_required
def change_password():
    from werkzeug.security import check_password_hash, generate_password_hash
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw     = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')
        if not check_password_hash(current_user.password, current_pw):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('participant.change_password'))
        if new_pw != confirm_pw:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('participant.change_password'))
        current_user.password = generate_password_hash(new_pw)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('participant.dashboard'))
    return render_template('participant/change_password.html')