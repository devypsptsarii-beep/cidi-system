from flask import Flask, render_template
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY']                  = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI']     = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail config
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

csrf = CSRFProtect(app)
mail = Mail(app)

from extensions import db, login_manager
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view        = 'auth.login'
login_manager.login_message     = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

from models import User

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

from routes.auth        import auth
from routes.admin       import admin
from routes.industry    import industry
from routes.participant import participant

app.register_blueprint(auth,        url_prefix='/auth')
app.register_blueprint(admin,       url_prefix='/admin')
app.register_blueprint(industry,    url_prefix='/industry')
app.register_blueprint(participant, url_prefix='/participant')

@app.route('/')
def index():
    from models import TrainingProgram
    open_programs = TrainingProgram.query.filter_by(status='open').all()
    return render_template('index.html', open_programs=open_programs)

@app.route('/about')
def about():
    return render_template('about.html')

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False') == 'True'
    app.run(debug=debug_mode)
