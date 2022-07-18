import os
import sys

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

# 初始化
mainApp = Flask(__name__)
mainApp.config.update(
    DEBUG=True,
    ENV='development'
)
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'
mainApp.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(mainApp.root_path, 'data.db')
mainApp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
db = SQLAlchemy(mainApp)


# 路由
@mainApp.route('/')
# @mainApp.route('/index')  失败，不能定义多个路由吗
def hello():
    # return render_template('origin_index.html', user=User.query.first(), movies=Movie.query.all())
    return render_template('index.html', movies=Movie.query.all())


@mainApp.route('/<username>')
def index(username):
    return 'hello visitor ' + username


@mainApp.route('/me')
def me():
    return render_template("about_me.html")


@mainApp.errorhandler(404)
def page_not_found(e):
    # return render_template('origin_404.html', user=User.query.first()), 404
    return render_template('404.html'), 404


@mainApp.context_processor  # 以后模板上下文有user了，render_template()可以不传入而直接使用了
def inject_user_data():
    return dict(user=User.query.first())      # 需要返回字典，等同于 return {'user': user}


# 数据库 设置表 ORM技术
class User(db.Model):  # 表名将会是 user（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))

    def __init__(self, name):
        self.name = name


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))

    def __init__(self, title, year):
        self.title = title
        self.year = year


if __name__ == '__main__':
    # 数据
    my_name = 'localh0st'
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
    db.session.add(User(name=my_name))  # db.session.add() 调用是将改动添加进数据库会话（一个临时区域）中。
    for record in watch_list:
        db.session.add(Movie(title=record['title'], year=record['year']))
    db.session.commit()  # commit() 很重要，只有调用了这一行才会真正把记录提交进数据库
    print('Done.')

    # print(User.query.all()[0].name)
    # for m in Movie.query.all():
    #     print(m.title)

    # run!
    mainApp.run()
