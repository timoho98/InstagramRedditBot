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
        if request.form['thing'] == 'Do Something':
            print "Do Something"
        elif request.form['thing'] == 'Do Something Else':
            print "Else"
        else:
            print "placeholder"
    return render_template("test.html")
@app.route('/listusers', methods = ['POST' , 'GET'])
def listusers():
    if request.method == 'POST':
        print request.form['id']
    return render_template("idlist.html", idlist = Instagrambot.jsonIdData)
@app.route('/listclick', methods = ['GET'])
def listget():
    getname = request.args.get('id')
    if Instagrambot.checkIfNameInData(getname):
        nameid = Instagrambot.getIdFromName(getname)
        print nameid
    print request.args.get('id')
    return render_template("listclick.html", id = nameid)
@app.route('/checkuser', methods = ['POST', 'GET'])
def checkuser():
    if request.method == 'POST':
        print request.form['submit']
    return render_template("usercheck.html", idlist = Instagrambot.jsonIdData, lastdate = Instagrambot.getListIdDate())
app.run()

