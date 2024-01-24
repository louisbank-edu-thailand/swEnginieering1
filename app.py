from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import datetime as dt

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
    leave_quota = db.Column(db.Integer, default=10)

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
    if 'logged_in' not in session or not session['logged_in']:
        return redirect('/login')

    #user_id = session.get('user_id')
    user_id = current_user.id
    user = UserObject.query.filter(UserObject.user_id == user_id).first()
    user_leave_quota = user.leave_quota

    print("Leave quota:")
    print(user.leave_quota)

    if request.method == 'POST':
        request_start_date = request.form.get('reqStartDate')
        request_end_date = request.form.get('reqEndDate')
        reason = request.form.get('reason')

        months_difference = (dt.datetime.strptime(request_start_date, "%Y-%m-%d").date() - dt.date.today()).days/30

        dt_leavestart = dt.datetime.strptime(request_start_date, "%Y-%m-%d").date()
        dt_leaveend = dt.datetime.strptime(request_end_date, "%Y-%m-%d").date()

        leave_duration = (dt_leaveend - dt_leavestart).days + 1

        if dt.datetime.strptime(request_start_date, "%Y-%m-%d").date() == dt.date.today():
            return "You cannot request a leave on the same day"
        elif months_difference > 2:
            return "You cannot request a leave more than 2 months in advance"
        elif leave_duration > user_leave_quota:
            return "You cannot request a leave more than your leave quota"
        else:
            new_request = Request(start_date=request_start_date, end_date=request_end_date, reason=reason,
                                  user_id=current_user.id)
            #subtract the leave_duration from UserObject leave_quota
            user.leave_quota = user.leave_quota - leave_duration
            print("new leave quota:")
            print(user.leave_quota)

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
            session['logged_in'] = True
            session['user_id'] = user.id
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
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect(url_for('home'))


@app.route('/deleteRequest/<int:id>')
def delete(id):
    req_to_delete = Request.query.get_or_404(id)

    request_date = dt.datetime.strptime(req_to_delete.start_date, "%Y-%m-%d").date()

    if request_date < dt.date.today():
        return "You cannot delete a request that has already passed"
    elif int(current_user.id) != int(req_to_delete.user_id):
        return "You cannot delete a request that is not yours."
    else:
        try:
            db.session.delete(req_to_delete)
            db.session.commit()
            return redirect(url_for('all_requests'))
        except:
            return 'There was an issue deleting your request'

if __name__ == '__main__':
    app.run(debug=True)
