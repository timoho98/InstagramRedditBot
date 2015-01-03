__author__ = 'Timothy'
import Instagrambot
import os
import datetime
from flask import Flask, render_template, request

app = Flask(__name__)
app.config['DEBUG'] = True
current_path = os.path.abspath(os.path.dirname(__file__))


def getLogFiles(dir_='./logs/'):
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


@app.route('/userclick', methods=['GET'])
def listget():
    getname = str(request.args.get('id'))
    if Instagrambot.checkIfNameInData(getname):
        userjson = Instagrambot.getJsonDict(getname)
        lastdate = datetime.datetime.utcfromtimestamp(int(userjson['lastdate'])).strftime('%Y-%m-%d %H:%M:%S')
        name = userjson['name']
        flairid = userjson['flairid']
        id_ = userjson['userid']
        return render_template("userclick.html", name=name, lastdate=lastdate, flairid=flairid, id=id_)
    else:
        print 'User Not Found'
        return render_template('User Not Found')
    print request.args.get('id')


@app.route('/checkuser')
def checkuser():
    return render_template("usercheck.html", idlist=Instagrambot.jsonIdData)


@app.route('/logs/')
def logsnoparam():
    filelist_ = getLogFiles()
    filelist_.sort()
    filelist_.reverse()
    return render_template("logs.html", filelist=filelist_)


# Expected format year-month-day
@app.route('/logs/<date>/')
def logs(date):
    print date
    with open(os.path.join(current_path + '\\logs', date)) as log:
        textInFile = log.read()
    textInFile = textInFile.split('\n')
    # return textInFile
    return render_template("logsshow.html", linelist=textInFile)


@app.route('/submitchanges', methods=['POST'])
def submitchanges():
    print request.form
    return 'placeholder'


app.run()




