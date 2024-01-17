from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this_is_insanely_secret_and_hard_to_crack'  # not secure
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_db.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


class UserObject(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    # requests = db.relationship('request', backref='user', lazy=True)

    def __repr__(self):
        return f"Request('{self.username}', '{self.password_hash}')"


class Request(db.Model):
    __tablename__ = 'request'
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.String(100), nullable=False)
    end_date = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)

    def __repr__(self):
        return (f"'({self.start_date}', '{self.end_date}', '{self.reason})'")


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/')
@app.route('/home')
def home():  # put application's code here
    return render_template('home.html')


@app.route('/all_requests')
@login_required
def all_requests():
    requests_with_username = db.session.query(Request, UserObject.username).join(UserObject).all()
    print(requests_with_username)
    return render_template('all_requests.html', requests_with_username=requests_with_username)


@app.route('/request', methods=['GET', 'POST'])
@login_required
def requests():
    if request.method == 'POST':
        request_start_date = request.form.get('reqStartDate')
        request_end_date = request.form.get('reqEndDate')
        reason = request.form.get('reason')
        print(request_start_date, request_end_date, reason)
        new_request = Request(start_date=request_start_date, end_date=request_end_date, reason=reason,
                              user_id=current_user.id)
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for('all_requests'))
    else:
        return render_template('request.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_id = None
        users = UserObject.query.all()
        for user in users:
            if user.username == username and user.password_hash == password:
                user_id = user.user_id
                break
        if user_id:
            user = User(user_id)
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('requests'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_id = None
        new_user = UserObject(username=username, password_hash=password)
        db.session.add(new_user)
        db.session.commit()

        users = UserObject.query.all()
        for user in users:
            if user.username == username and user.password_hash == password:
                user_id = user.user_id
                break

        if user_id:
            user = User(user_id)
            login_user(user)
            flash('Register and Login successful!', 'success')
            return redirect(url_for('requests'))
        else:
            flash('Something went wrong, try again', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful!', 'success')
    return redirect(url_for('home'))


@app.route('/deleteRequest/<int:id>')
def delete(id):
    req_to_delete = Request.query.get_or_404(id)

    try:
        db.session.delete(req_to_delete)
        db.session.commit()
        return redirect(url_for('all_requests'))
    except:
        return 'There was an issue deleting your task'


if __name__ == '__main__':
    app.run(debug=True)
