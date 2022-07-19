from flask import Flask, render_template, request, url_for, redirect, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import sys

# 初始化
mainApp = Flask(__name__)
mainApp.config.update(
    DEBUG=True,
    ENV='development'
)

mainApp.config['SECRET_KEY'] = 'localh0st'  # 等同于 mainApp.secret_key = 'localh0st' 设置密钥,数据库用
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'
mainApp.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(mainApp.root_path, 'data.db')
mainApp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
db = SQLAlchemy(mainApp)

login_manager = LoginManager(mainApp)
login_manager.login_view = 'login'  # 未登录用户访问无权限url时重定向到login


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))


# 路由
@mainApp.route('/', methods=['GET', 'POST'])
# @mainApp.route('/index')  失败，不能定义多个路由吗
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect('/')
        title = request.form.get('title')  # 传入表单对应输入字段的 name 值
        year = request.form.get('year')
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')  # flash() 函数在内部会把消息存储到 Flask 提供的 session 对象里。session 用来在请求间存储数据
            return redirect('/')  # 重定向
        db.session.add(Movie(title=title, year=year, belongs_to=current_user.username))
        db.session.commit()
        flash('Item created.')
        return redirect('/')
    else:  # GET
        # return render_template('origin_index.html', user=User.query.first(), movies=Movie.query.all())
        if current_user.is_authenticated:
            return render_template('index.html', movies=Movie.query.filter(Movie.belongs_to == current_user.username).all())
        else:   # 未登录仅展示admin的watch list
            return render_template('index.html', movies=Movie.query.filter(Movie.belongs_to == 'admin').all())


@mainApp.route('/<username>')
def hello(username):
    return 'hello visitor ' + username


@mainApp.route('/me')
def me():
    return render_template("about_me.html")


@mainApp.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  # url_for('edit', movie_id=2) 会生成 /movie/edit/2
        movie = Movie.query.get_or_404(movie_id)  # movie_id是主键
        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Item updated.')
        return redirect('/')
    else:
        return render_template('edit.html', movie=Movie.query.get_or_404(movie_id))


@mainApp.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(movie_id):
    db.session.delete(Movie.query.get_or_404(movie_id))
    db.session.commit()
    flash('Item Deleted.')
    return redirect('/')


@mainApp.errorhandler(404)
def page_not_found(e):
    # return render_template('origin_404.html', user=User.query.first()), 404
    return render_template('404.html'), 404


@mainApp.context_processor  # 以后模板上下文有user了，render_template()可以不传入而直接使用了
def inject_data():
    return dict(user=current_user, message=get_flashed_messages())  # 需要返回字典，等同于 return {'user': user}


@mainApp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:  # 空字符
            flash('Invalid input.')
            return redirect(url_for('login'))
        user = User.query.filter(User.username == username).first()
        if not user:  # 没查到已注册的user
            flash('No user founded.')
            return redirect(url_for('register'))
        if user.validate_passwd(password):
            login_user(user)
            flash('Login success.')
            return redirect('/')
        else:
            flash('Invalid password.')
            return redirect(url_for('login'))
    else:  # GET
        return render_template('login.html')


@mainApp.route('/logout')
@login_required  # 视图保护
def logout():
    logout_user()
    flash('Logout success')
    return redirect('/')


@mainApp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        new_name = request.form['name']
        if not new_name or len(new_name) > 20:
            flash('Invalid new name.')
            return redirect(url_for('settings'))
        current_user.name = new_name
        db.session.commit()
        flash('Settings updated')
        return redirect('/')
    else:
        return render_template('settings.html')


@mainApp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        if not new_username or not new_password:    # 空
            flash('Invalid username or password.')
            return redirect(url_for('register'))
        if User.query.filter(User.username == new_username).count():     # 重名
            flash('Username occupied.')
            return redirect(url_for('register'))
        new_user = User('Default name')
        new_user.set_username(new_username)
        new_user.set_passwd(new_password)
        new_user.set_group('user')
        db.session.add(new_user)
        db.session.commit()
        flash('Register success.')
        return redirect(url_for('login'))
    else:
        return render_template('register.html')


# 数据库 设置表 ORM技术
class User(db.Model, UserMixin):  # 表名将会是 user（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    passwd_hash = db.Column(db.String(128))
    group = db.Column(db.String(10))  # admin operator user

    def __init__(self, name):
        self.name = name

    def set_username(self, username):
        self.username = username

    def set_passwd(self, pswd):
        self.passwd_hash = generate_password_hash(pswd)

    def validate_passwd(self, pswd):
        return check_password_hash(self.passwd_hash, pswd)

    def set_group(self, group):
        self.group = group


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))
    belongs_to = db.Column(db.String(20))   # using username

    def __init__(self, title, year, belongs_to):
        self.title = title
        self.year = year
        self.belongs_to = belongs_to


if __name__ == '__main__':
    # 数据
    watch_list = [
        {'title': '喜剧之王', 'year': '1999'},
        {'title': '食神', 'year': '1996'},
        {'title': '2046', 'year': '2004'},
        {'title': '重庆森林', 'year': '1994'},
        {'title': '旺角卡门', 'year': '1988'}
    ]

    # 创建表和数据库文件, 如果改动了模型类，想重新生成表模式，那么需要先使用 db.drop_all() 删除表，然后重新创建：
    db.drop_all()  # db.drop_all() 会一并删除所有数据
    db.create_all()  # 新建空数据库和表
    # 添加数据
    print('Adding records...')
    me = User(name='localh0st')
    me.set_group('admin')
    me.set_username('admin')
    me.set_passwd('123')
    db.session.add(me)  # db.session.add() 调用是将改动添加进数据库会话（一个临时区域）中。
    for record in watch_list:
        db.session.add(Movie(title=record['title'], year=record['year'], belongs_to='admin'))
    db.session.commit()  # commit() 很重要，只有调用了这一行才会真正把记录提交进数据库
    print('Done.')

    # print(User.query.all()[0].name)
    # for m in Movie.query.all():
    #     print(m.title)

    # run!
    mainApp.run()
