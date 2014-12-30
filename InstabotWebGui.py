__author__ = 'Timothy'
import Instagrambot, os
from flask import Flask, render_template, request

app = Flask(__name__)
app.config['DEBUG'] = True
current_path = os.path.abspath(os.path.dirname(__file__))


def getLogFiles(dir_='./'):
    filelist = []
    for file in os.listdir(dir_):
        if file.endswith(".log"):
            filelist.append(file)
    return filelist


@app.route('/')
def hello_world():
    return render_template("Index.html")


@app.route('/testrender', methods=['POST', 'GET'])
def testrender():
    if request.method == 'POST':
        if request.form['thing'] == 'Do Something':
            print "Do Something"
        elif request.form['thing'] == 'Do Something Else':
            print "Else"
        else:
            print "placeholder"
    return render_template("test.html")


@app.route('/listusers', methods=['POST', 'GET'])
def listusers():
    if request.method == 'POST':
        print request.form['id']
    return render_template("idlist.html", idlist=Instagrambot.jsonIdData)


@app.route('/listclick', methods=['GET'])
def listget():
    getname = request.args.get('id')
    if Instagrambot.checkIfNameInData(getname):
        nameid = Instagrambot.getIdFromName(getname)
        print nameid
    print request.args.get('id')
    return render_template("listclick.html", id=nameid)


@app.route('/checkuser', methods=['POST', 'GET'])
def checkuser():
    if request.method == 'POST':
        print request.form['submit']
    return render_template("usercheck.html", idlist=Instagrambot.jsonIdData, lastdate=Instagrambot.getListIdDate())

@app.route('/logs/')
def logsnoparam():
    return render_template("logs.html")

# Expected format year-month-day
@app.route('/logs/<date>/')
def logs(date):
    print date
    with open(os.path.join(current_path, date+ ".log")) as log:
        textInFile = log.read()
    textInFile = textInFile.split('\n')
    # return textInFile
    return render_template("logsshow.html", linelist=textInFile)

app.run()

