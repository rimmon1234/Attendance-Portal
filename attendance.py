from flask import Flask,render_template, redirect, request, session, flash, url_for, send_file
from datetime import timedelta, datetime, date
import pandas as pd
import io
from flask_sqlalchemy import SQLAlchemy


username = 'JayantaDas' #Username For Login
passw = 'smartEd@5500' #Password For Login
today = date.today()
day_of_week = today.strftime("%A")

app = Flask(__name__)
app.secret_key = 'hello'
app.permanent_session_lifetime = timedelta(hours= 4)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entry.db'
app.config['SQLALCHEMY_BINDS'] = {'two' : 'sqlite:///view.db'}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()

#Entry Database Schema Start
class EntryData(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False)
    entry_time = db.Column(db.String(200), default= datetime.now().strftime("%H:%M:%S"))
    exit_time = db.Column(db.String(200))

    def __repr__(self) -> str:
        return f'{self.sno} - {self.name}'
#Entry Database Schema End

#View Database Schema Start
class PreviousSession(db.Model):
    __bind_key__ = 'two'
    sno = db.Column(db.Integer, primary_key = True)
    class_desc = db.Column(db.String(200), default = 'Normal Class')
    date = db.Column(db.DateTime, default = datetime.now)
    day = db.Column(db.String(200))

    def __repr__(self) -> str:
        return f'{self.sno} - {self.date}'
#View Database Schema End

with app.app_context():
    db.create_all()

#App Login Page Start
@app.route("/", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        user = request.form['name']
        password = request.form['passwd']
        checked = request.form.get('Remember me')
        if user == username and passw == password:
            if checked=='Remember me':
                session.permanent = True
            session['user'] = user
            session['password'] = password
            flash(f'You Have Logged In Successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash(f'Username Or Password Is Not Correct! Try Again', 'error')
            return redirect(url_for('login'))

    else:
        if 'user' in session:
            flash('Already Logged In!', 'info')
            return redirect(url_for('home'))
        return render_template('login.html')

@app.route('/home', methods = ['POST', 'GET'])
def home():
    if 'user' in session:
        allEntry = EntryData.query.all()
        return render_template('home.html',  allEntry = allEntry)
    else:
        flash('You Are Not Logged In', 'info')
        return redirect(url_for('login'))
#App Login Page End

#App Logout Start
@app.route('/logout')
def logout():
    if 'user' in session:
        flash(f'You Have Been Logged Out Successfully', 'info')
    session.pop('user', None)
    session.pop('password', None)
    return redirect(url_for('login'))
#App Logout End


#App Entry Data Page Start
@app.route('/entry', methods = ['GET', 'POST'])
def data_entry():
    
    if 'user' in session:
    
        if request.method == 'POST':
            name = request.form.get('name')
            entry = EntryData(name = name)
            db.session.add(entry)
            db.session.commit()
    
        allEntry = EntryData.query.all()
        if len(allEntry) == 0:
            start_session = PreviousSession(day = day_of_week)
            db.session.add(start_session)
            db.session.commit()
        return render_template('data_create.html', allEntry = allEntry)
    else:
        flash('You Are Not Logged In', 'info')
        return redirect(url_for('login'))
#App Entry Data Page End

#App Change Start
@app.route('/change/<int:sno>', methods = ['POST', 'GET'])
def change(sno):
    if 'user' in session:
        if request.method == 'POST':
            name = request.form.get('name')
            allEntry = EntryData.query.filter_by(sno = sno).first()
            allEntry.name = name
            db.session.add(allEntry)
            db.session.commit()
            return redirect('/entry')
        allEntry = EntryData.query.filter_by(sno = sno).first()
        return render_template('change.html', allEntry = allEntry)
    else:
        flash('You Are Not Logged In', 'info')
        return redirect(url_for('login'))
#App Change End

#App Update Start
@app.route('/update/<int:sno>')
def update(sno):
    if 'user' in session:
        allEntry = EntryData.query.filter_by(sno = sno).first()
        allEntry.exit_time = datetime.now().strftime("%H:%M:%S")
        db.session.add(allEntry)
        db.session.commit()
        return redirect('/entry')
    else:
        flash('You Are Not Logged In', 'info')
        return redirect(url_for('login'))
    
#App Update End

#End Session And Save Button Start
@app.route('/end_session')
def end_session():
    if 'user' in session:
        allEntry = EntryData.query.all()
        for item in allEntry:
            db.session.delete(item)
        db.session.commit()
        return redirect('/home')
    else:
        flash('You Are Not Logged In', 'info')
        return redirect(url_for('login'))
#End Session And Save Buttion End

#Delete Entry Start
@app.route('/delete/<int:sno>')
def delete(sno):
    if 'user' in session:
        allEntry = EntryData.query.filter_by(sno = sno).all()
        for entry in allEntry:
            db.session.delete(entry)
            db.session.commit()
        return redirect('/entry')
    else:
        flash('You Are Not Logged In', 'info')
        return redirect(url_for('login'))
#Delete Entry End

#Save File Start
@app.route('/export')
def export():
    if 'user' in session:
        all_entries = EntryData.query.all()

        data = []
        for entry in all_entries:
            data.append({
                'Sno': entry.sno,
                'Name': entry.name,
                'Entry Time': entry.entry_time,
                'Exit Time': entry.exit_time
            })

        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name= 'Attendance' )
            writer.close()
        
        output.seek(0)
        return send_file(output, download_name= f"Attendance_{today}.xlsx", as_attachment=True)
    else:
        flash('You Are Not Logged In', 'info')
        return redirect(url_for('login'))
#Save File End

#Session View Start
@app.route('/view_session')
def view_session():
    if 'user' in session:
        allEntry = PreviousSession.query.all()
        return render_template('session_view.html',  allEntry = allEntry)
    else:
        flash('You Are Not Logged In', 'info')
        return redirect(url_for('login'))
#Session View End

#Session View Entry Update Start
@app.route('/session_change/<int:sno>', methods = ['POST', 'GET'])
def session_view_change(sno):
    if 'user' in session:
        if request.method == 'POST':
            desc = request.form.get('desc')
            Entry = PreviousSession.query.filter_by(sno = sno).first()
            Entry.class_desc = desc
            db.session.add(Entry)
            db.session.commit()
            return redirect('/view_session')
        Entry = PreviousSession.query.filter_by(sno = sno).first()
        return render_template('view_session_change.html', Entry = Entry)
    else:
        flash('You Are Not Logged In', 'info')
        return redirect(url_for('login'))
#Session View Entry Update End

#Session View Entry Delete Start
@app.route('/session_delete/<int:sno>')
def session_view_delete(sno):
    if 'user' in session:
        allEntry = PreviousSession.query.filter_by(sno = sno).all()
        for entry in allEntry:
            db.session.delete(entry)
            db.session.commit()
        return redirect('/view_session')
    else:
        flash('You Are Not Logged In', 'info')
        return redirect(url_for('login'))
#Session View Entry delete End
if __name__ == '__main__':
    app.run(debug=True)