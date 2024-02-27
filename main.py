from flask import Flask, render_template, redirect, url_for, flash, session, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, DateField, TimeField, \
    SelectField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.orm import joinedload
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Change this to a secure random key
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.init_app(app)


# database model for normal users
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# data model for admin users
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

        # Define the is_active property

    @property
    def is_active(self):
        return True


# database model to add sermons
class Sermon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    speaker = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Sermon('{self.title}', '{self.speaker}', '{self.date}')"


# database model to add tithing records
class TithingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tithing_records', lazy=True))
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"TithingRecord(user_id={self.user_id}, amount={self.amount}, date={self.date})"


class SundayServiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(100))
    category = db.Column(db.String(50), nullable=False)


# Define forms for registration, login, sermon, tithing record, and service item
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    is_admin = BooleanField('Register as admin')
    submit = SubmitField('Register')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Email already registered.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class SermonForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    speaker = StringField('Speaker', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])


class TithingRecordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Add Tithing Record')


class AddServiceItemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    location = StringField('Location')
    category = SelectField('Category', choices=[('Worship', 'Worship'), ('Sermon', 'Sermon'), ('Prayer', 'Prayer')],
                           validators=[DataRequired()])
    submit = SubmitField('Add Service Item')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes for different pages

@app.route("/index")
def index():
    sunday_service_items = SundayServiceItem.query.all()

    return render_template("index.html", username=current_user.username if current_user.is_authenticated else None,
                           sunday_service_items=sunday_service_items)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if the user wants to register as an admin
        if form.is_admin.data:
            # Create admin user
            admin = Admin(username=form.username.data, email=form.email.data)
            admin.set_password(form.password.data)
            db.session.add(admin)
            db.session.commit()
            flash('Admin user created successfully!', 'success')
        else:
            # Create regular user
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Check if the submitted credentials match admin credentials
        admin = Admin.query.filter_by(email=form.email.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            flash('You have been logged in as an admin!', 'success')
            return redirect(url_for('add_user'))  # Redirect to admin dashboard
        # If admin credentials are not matched, proceed with regular user login
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            user.set_password(form.password.data)
            db.session.commit()
            login_user(user)
            flash('You have been logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    form = LoginForm()

    if form.validate_on_submit():
        if form.email.data == admin_email and bcrypt.check_password_hash(admin_password_hash, form.password.data):
            session['admin_logged_in'] = True
            flash('Successfully logged in as admin', 'success')
            return redirect(url_for('add_user'))
        else:
            flash('Admin login unsuccessful. Please check email and password', 'danger')

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))


@app.route('/add_user')
@login_required
def add_user():
    return render_template('Admin/add_user.html')


@app.route('/View_users')
@login_required
def view_users():
    users = User.query.all()
    return render_template('Admin/view_users.html', users=users)


@app.route('/add sermon', methods=['POST'])
def add_sermon():
    form = SermonForm()
    if form.validate_on_submit():
        sermon = Sermon(
            title=form.title.data,
            speaker=form.speaker.data,
            date=form.date.data,
            description=form.description.data
        )
        db.session.add(sermon)
        db.session.commit()
        flash('sermon added successfully')
        return redirect(url_for('add_sermon'))  # Redirect to home page after adding sermon
    return render_template('Admin/add_sermon.html', form=form)


@app.route('/add_service', methods=['GET', 'POST'])
@login_required
def add_service():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time_str = request.form['time']  # Get the time string from the form
        time = datetime.strptime(time_str, '%H:%M').time()  # Convert the string to a Python time object
        location = request.form['location']
        category = request.form['category']

        new_service_item = SundayServiceItem(title=title, description=description, date=date, time=time,
                                             location=location, category=category)
        db.session.add(new_service_item)
        db.session.commit()
        flash('Service item added successfully!', 'success')
        return redirect(url_for('add_service'))

    return render_template('Admin/add_service.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        # Logic for admin dashboard
        return render_template('Admin/add_user.html')
    else:
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route("/add_tithe", methods=["GET", "POST"])
@login_required
def add_tithe():
    form = TithingRecordForm()
    if form.validate_on_submit():
        username = form.username.data
        user = User.query.filter_by(username=username).first()
        if user:
            tithing_record = TithingRecord(
                user_id=user.id,
                username=username,
                amount=form.amount.data,
                date=form.date.data
            )
            db.session.add(tithing_record)
            db.session.commit()
            flash('Tithing record added successfully', 'success')
            return redirect(url_for('add_tithe'))
        else:
            flash('User does not exist add new user', 'danger')
            return redirect(url_for('add_user'))
    return render_template('Admin/add_tithe.html', form=form)


@app.route("/view_tithing_records")
@login_required
def view_tithing_records():
    tithing_records = current_user.tithing_records
    return render_template("view_tithe.html", tithing_records=tithing_records)


@app.route('/download_tithing_records_pdf/<int:tithing_id>')
def download_tithing_records_pdf(tithing_id):
    tithing_record = TithingRecord.query.get(tithing_id)
    pdf_data = generate_pdf(tithing_record)

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=tithing_record_{tithing_id}.pdf'

    return response


def generate_pdf(tithing_record):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    # Add tithing record data to the PDF
    p.drawString(100, 750, f"Amount: ${tithing_record.amount}")
    p.drawString(100, 720, f"Date: {tithing_record.date}")

    # Check if the 'username' attribute exists in the tithing_record object
    if hasattr(tithing_record, 'username'):
        p.drawString(100, 690, f"Added by: {tithing_record.username}")
    else:
        p.drawString(100, 690, "Added by: Anonymous")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


@app.route('/sermon')
@login_required
def display_sermon():
    sermons = Sermon.query.all()
    return render_template('sermon.html', sermons=sermons)


# Ensure this is at the end of your script to run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
