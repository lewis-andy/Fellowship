from flask import Flask, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate  # Import Flask-Migrate
from wtforms import BooleanField
from wtforms.fields import DateField, TextAreaField
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SubmitField
from wtforms.validators import DataRequired
from flask import render_template, redirect, url_for, flash
from datetime import datetime
from wtforms import SelectField
from flask import render_template, request, jsonify
from sqlalchemy.orm import joinedload

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Change this to a secure random key
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


# database model for users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


def validate_email(field):
    if User.query.filter_by(email=field.data).first():
        raise ValidationError('Email already exists.')


# database model to adding sermons
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
    username = db.Column(db.String(100), nullable=False)  # Add username field
    user = db.relationship('User', backref=db.backref('tithing_records', lazy=True))
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"TithingRecord(user_id={self.user_id}, username={self.username}, amount={self.amount}, date={self.date})"


# defines the pass words of the admin page
admin_username = 'Lewis'
admin_password = 'Andanje'
admin_email = 'lewisandanje3@gmail.com'


# define the class to registration db module
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('submit')


#   Login class form of the db module very essential

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')


# class form to adding sermons
class SermonForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    speaker = StringField('Speaker', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])


# class to tithing record form
class TithingRecordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Add Tithing Record')


# index html the loading page route
@app.route("/index")
def index():
    return render_template("index.html")


# contact us route
@app.route("/contact")
def contact():
    return render_template("contact.html")


# about page route
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/display_sermon")
def display_sermon():
    sermons = Sermon.query.all()
    return render_template("sermon.html", sermons=sermons)  # Pass sermons instead of Sermon


# route page to the register form page. Defines the registration route details
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template("register.html", form=form)


# it is the main route of the bage when user loads it it takes from here. define login system
@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()  # call the login form
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        # Check if admin credentials are entered
        if email == admin_email and password == admin_password:
            session['admin_logged_in'] = True
            return redirect(url_for('add_user'))

        # performing login authentication assuming all neccessary logic

        if user and bcrypt.check_password_hash(user.password, password):
            flash('Login successful!', 'success')
            # Here you can redirect to another page after login
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')

    return render_template("login.html", form=form)


# Admins page to add users to the system
@app.route('/Admin/add_user')
def add_user():
    if 'admin_logged_in' in session:
        return render_template('Admin/add_user.html')
    else:
        return redirect(url_for('login')) @ app.route('/add_sermon', methods=['GET', 'POST'])


# route to the add_sermon add_sermon page
@app.route('/Admin/add_sermon', methods=['GET', 'POST'])
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
        return redirect(url_for('add_user'''))  # Redirect to home page after adding sermon

    return render_template('Admin/add_sermon.html', form=form)


# admin page to view the current users registered fetches it from the database.
@app.route("/Admin/view_users")
def view_users():
    users = User.query.all()
    return render_template("Admin/view_users.html", users=users)


# function to delete users from  the table
@app.route("/delete_user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    users = [user_id]
    user_index = next((index for index, user in enumerate(users) if user["id"] == user_id), None)
    if user_index is not None:
        del users[user_index]
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        return jsonify({"message": "User not found"}), 404


# code to add tithing record from admin panel
@app.route('/add_tithe', methods=['GET', 'POST'])
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
            flash('User does not exist', 'danger')
            return redirect(url_for('add_user'))
    return render_template('Admin/add_tithe.html', form=form)


# a code to call off the program
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
