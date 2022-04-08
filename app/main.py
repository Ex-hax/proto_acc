import click
from flask import Flask, request, redirect,url_for, flash, render_template,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import database_exists, create_database, drop_database
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, UserMixin,login_user, logout_user, current_user

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.datastructures import ImmutableMultiDict

from datetime import datetime

app = Flask(__name__)

DB_URL = 'postgresql://postgres:1234@localhost:5432/ACCTEST'#'postgresql://postgres:postgres@localhost:5432/ACCTEST'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SECRET_KEY'] = '00$9YMJS1SwgazTFUA9$9dda1147a8'
db = SQLAlchemy(app)
migrate = Migrate(app, db) 

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

'''Master data for User'''		 
class User(UserMixin, db.Model): #Master and one time compute
	__tablename__ = 'users'
	
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(),unique=True,nullable=False)
	password = db.Column(db.String(),unique=False,nullable=False)
	email = db.Column(db.String(),unique=True,nullable=False)
	is_admin = db.Column(db.Boolean())
	
	def __init__(self,username,password,email,is_admin):
		self.username = username
		self.password = generate_password_hash(password)
		self.email = email
		self.is_admin = is_admin
	
	def verify_password(self,pwd):
		return check_password_hash(self.password,pwd)
	
	def __repr__(self):
		return f'id:{self.id}, username:{self.username}, password:{self.password}, email:{self.email}, is_admin:{self.is_admin}\n'

class LoginForm(FlaskForm):
	username = StringField('Username',validators=[DataRequired()])
	password = PasswordField('Password',validators=[DataRequired()])
	submit = SubmitField('Submit')
	
@login_manager.user_loader
def load_user(user_id):
	#print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>',user_id)
	return User.query.get(int(user_id))

'''Master data for Income outcome etc.'''
class iocome(db.Model):
	__tablename__ = 'inoutcome'

	id = db.Column(db.Integer, primary_key=True, nullable=False)
	user_id = db.Column(db.Integer())
	display_user_id = db.Column(db.Integer())
	idate = db.Column(db.DateTime(), default=datetime.utcnow)
	item = db.Column(db.Integer())	
	income = db.Column(db.Float())
	outcome = db.Column(db.Float())
	remain = db.Column(db.Float())
	description = db.Column(db.String())
	
	def __init__(self,user_id,display_user_id,idate,item,income,outcome,remain,description):
		self.user_id = user_id
		self.display_user_id = display_user_id
		self.idate = idate
		self.item = item
		self.income = income
		self.outcome = outcome
		self.remain = remain
		self.description = description
	
	def __repr__(self):
		return f'{self.id},{self.user_id},{self.display_user_id},{self.idate},{self.item},{self.income},{self.outcome},{self.remain},{self.description}\n'
	
'''Login logout signup'''	 
@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))

@app.route('/signup/regis',methods=['POST'])
def regis():
	if request.method == 'POST':
		new_name = request.form['username']
		new_pw = request.form['password']
		new_email = request.form['email']
		
		new_user_name = User.query.filter_by(username=new_name).all()
		#new_user_password = User.query.filter_by(password=generate_password_hash(new_pw))
		new_user_email = User.query.filter_by(email=new_email).all()
		
		unmatch_username = True
		#unmatch_userpassword = True
		unmatch_useremail = True
		
		if new_user_name:
			flash(f'This username {new_name} already taken.')
			unmatch_username = False
		# if new_user_password:
			# flash('This password already taken.')
			# unmatch_userpassword = False
		if new_user_email:
			flash(f'This e-mail {new_email} already taken.')
			unmatch_useremail = False
		
		if unmatch_username & unmatch_useremail: #unmatch_userpassword &
			db.session.add(User(username=new_name,password=new_pw,email=new_email,is_admin=False))
			db.session.commit()
			return redirect(url_for('login'))
		else:
			return redirect(url_for('signup'))
			
@app.route('/signup',methods=['GET','POST'])
def signup():
	return render_template('signup.html')
 
@app.route('/login',methods=['GET','POST'])
def login():
	form = LoginForm()
	username = form.username.data
	password = form.password.data
	if form.validate_on_submit():
		user = User.query.filter_by(username=username).first()
		if user and user.verify_password(password):
			login_user(user)
			return redirect(url_for('homepage'))
		else:
			flash('This user does not exist or password was incorrect.')
	else:
		pass
	return render_template('login.html',form=form)
	
@app.route('/')
def to_login():
	return redirect(url_for('login'))	
'''Home page'''	   
@app.route('/homepage')
@login_required
def homepage():
	if '_user_id' in session.keys():
		isadmin = db.session.query(User).get(session['_user_id']).is_admin
		uid = {'is_admin' : isadmin, 'cur_usr_name' : db.session.query(User).get(session['_user_id']).username, 'cur_usr_id' : session['_user_id']}

	if isadmin == True:
		datas = iocome.query.order_by(iocome.id.asc()).all()
	else:
		datas = iocome.query.filter_by(display_user_id=session['_user_id']).order_by(iocome.id.asc())

	final_data = [{
	'id' : i.id,
	'user_id' : i.user_id,
	'display_user_id' : i.display_user_id,
	'user_name' : db.session.query(User).get_or_404(i.user_id).username, #db.session.query(User.username).filter_by(id=i.user_id).first()
	'date' : i.idate,
	'item' : i.item,
	'income' : i.income,
	'outcome' : i.outcome,
	'remain' : i.remain,
	'description' : i.description
	} for i in datas]
	
	return render_template('index.html',cur_usr = uid,final_data=final_data)
	
'''For create new data'''
@app.route('/homepage/create')
@login_required
def create():
	cid = {'cur_usr_name' : db.session.query(User).get(session['_user_id']).username}
	return render_template('create.html',cur_usr=cid)
	
@app.route('/homepage/create/save',methods=['POST'])
@login_required
def save():
	if request.method == 'POST':
		description = request.form['des']
		income = request.form['income']
		outcome = request.form['outcome']
		remain = request.form['remain']
		dateissue = datetime.fromisoformat(request.form['dateissue'])#dateissue = request.form['dateissue']
		try: #Maybe check with NoneType
			u = int(db.session.query(iocome).filter_by(user_id=session['_user_id']).order_by(iocome.item.desc()).first().item) + 1
		except:
			u = 1
		uu = iocome(user_id=session['_user_id'],display_user_id=session['_user_id'],idate=dateissue,item=u,income=income,outcome=outcome,remain=remain,description=description)
		db.session.add(uu)
		db.session.commit()
		
	return redirect(url_for('homepage'))
'''For edit'''
@app.route('/homepage/edit/lid=<line_id>',methods=['POST','GET'])
@login_required
def editpage(line_id):
	uid = {'lid' : line_id, 'cur_usr_name' : db.session.query(User).get(session['_user_id']).username}
	edit_data = iocome.query.filter_by(id = line_id)
	
	ed = [{'id' : i.id, 
	'item' : i.item, 
	'income' : i.income, 
	'outcome' : i.outcome, 
	'remain' : i.remain, 
	'description' : i.description,
	'dateissue' : i.idate
	} for i in edit_data]
	
	return render_template('edit_data.html',cur_usr=uid,edata = ed)

@app.route('/homepage/edit/update',methods=['POST','GET'])
@login_required
def update():
	update_data = iocome.query.get(request.form['lid'])
	if request.method == 'POST':
		update_data.user_id = session['_user_id'] #
		update_data.item = request.form['item']
		update_data.income = request.form['income']
		update_data.outcome = request.form['outcome']
		update_data.remain = request.form['remain']
		update_data.idate = datetime.fromisoformat(request.form['dateissue'])
		update_data.description = request.form['des']
		db.session.add(update_data)
		db.session.commit()
		
	return redirect(url_for('homepage'))
'''For delete'''	
@app.route('/homepage/delete/<line_id>',methods=['GET'])
@login_required 
def delete(line_id):
	u = iocome.query.get_or_404(line_id)
	db.session.delete(u)
	db.session.commit()
	return redirect(url_for('homepage'))
'''report'''
'''setting'''
@app.route('/homepage/setting')
@login_required
def setting():
	if db.session.query(User).get_or_404(session['_user_id']).is_admin == False: return redirect(url_for('homepage'))
	uid = {'cur_usr_name' : db.session.query(User).get(session['_user_id']).username}
	users = db.session.query(User).order_by(User.id.asc()).all()
	all_users = [{
	'user_id' : u.id,
	'username' : u.username,
	'user_email' : u.email,
	'is_admin' : u.is_admin
	} for u in users]
	return render_template('setting.html',cur_usr=uid,udata=all_users)

@app.route('/homepage/setting/change',methods=['POST'])
@login_required
def setting_change():
	if request.method == 'POST':
		data = request.form
		for d in range(len(data.getlist('user_id'))): #admin +- and reset password
			prepare_user = User.query.get_or_404(int(data.getlist('user_id')[d]))
			if data.getlist('oc_is_admin')[d] == 'true':
				prepare_user.is_admin = True
			else:
				prepare_user.is_admin = False
			
			if data.getlist('reset_password')[d] != '':
				prepare_user.password = generate_password_hash(data.getlist('reset_password')[d])
				
			db.session.add(prepare_user)
			db.session.commit()
		
		for de in range(len(data.getlist('user_id'))): #delete user and data
			prepare_del_user_data_ids = db.session.query(iocome).filter_by(display_user_id = int(data.getlist('user_id')[de]))
			
			prepare_del_user_data_id =[{i.id} for i in prepare_del_user_data_ids]
			
			for a in range(len(prepare_del_user_data_id)):
				if data.getlist('oc_is_delete')[de] == 'true':
					db.session.delete(iocome.query.get_or_404(prepare_del_user_data_id[a]))
					db.session.commit()

			prepare_del_user = db.session.query(User).get_or_404(int(data.getlist('user_id')[de]))
			if data.getlist('oc_is_delete')[de] == 'true':
				db.session.delete(prepare_del_user)
				db.session.commit()
			
			#create if else to delete data in table users and inoutcome
		return redirect(url_for('homepage'))		
'''Database part'''
@app.cli.command('cli')
@click.argument('cr')
@app.route('/cli<cr>',methods=['GET'])
def db_manager(cr):
	if cr == 'c' or cr == 'C' :
		if not database_exists(DB_URL):
			create_database(DB_URL)
			db.create_all()
			sys_user = User(username='admin', password='****', email='test@test.com',is_admin=True)
			db.session.add(sys_user)
			db.session.commit()
			print('xxxxxxxxxxxxxxx db and table created xxxxxxxxxxxxxx')
			return '<h1>db and table created</h1>'
		else:
			print('xxxxxxxxxxxxxxx No db and table was created xxxxxxxxxxxxxx')
			return '<h1>No db and table was created</h1>'
	if cr == 'd' or cr == 'D':
		drop_database(DB_URL)
		print('xxxxxxxxxxxxxxx db and table deleted xxxxxxxxxxxxxx')
		return '<h1>db and table deleted</h1>'