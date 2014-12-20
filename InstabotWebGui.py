__author__ = 'Timothy'
import Instagrambot
from flask import Flask, render_template, request

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/')
def hello_world():
    return render_template("Index.html")
@app.route('/testrender', methods = ['POST' , 'GET'])
def testrender():
    if request.method == 'POST':
        if request.form['submit'] == 'Do Something':
            print "Do Something"
        elif request.form['submit'] == 'Do Something Else':
            print "Else"
        else:
            print "placeholder"
    return render_template("test.html")
@app.route('/listusers')
def listusers():
    return render_template("idlist.html", idlist = Instagrambot.jsoniddata)
@app.route('/checkuser', methods = ['POST', 'GET'])
def checkuser():
    if request.method == 'POST':
        print request.form['submit']
    return render_template("usercheck.html", idlist = Instagrambot.jsoniddata, lastdate = Instagrambot.getlistiddate())
app.run()

