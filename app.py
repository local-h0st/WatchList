from flask import Flask, render_template

# print(__name__)   '__main__'
mainApp = Flask(__name__)

my_name = 'localh0st'

watch_list = [
    {'title': '喜剧之王', 'year': '1999'},
    {'title': '食神', 'year': '1996'},
    {'title': '2046', 'year': '2004'},
    {'title': '重庆森林', 'year': '1994'},
    {'title': '旺角卡门', 'year': '1988'}
]


@mainApp.route('/')
def hello():
    return render_template('index.html', username=my_name, movies=watch_list)


@mainApp.route('/<username>')
def index(username):
    return 'hello visitor ' + username


@mainApp.route('/me')
def me():
    return '<h>a developer named localh0st</h>'


if __name__ == '__main__':
    mainApp.config.update(
        DEBUG=True,
        ENV='development'
    )
    mainApp.run()
