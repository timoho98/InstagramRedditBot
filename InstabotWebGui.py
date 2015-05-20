__author__ = 'Timothy'
import Instagrambot
import os
import datetime
import time
import ConfigParser
import threading
from flask import Flask, render_template, request

app = Flask(__name__)
app.config['DEBUG'] = True
current_path = os.path.abspath(os.path.dirname(__file__))
# Load Config
config = ConfigParser.ConfigParser()
config.read(os.path.join(current_path, 'config.ini'))

# Variables that are checked in thread
interval = config.get("ScriptSettings", "Interval")
updateDates = False
checkAllNow = False
updateTime = False
checkUser = False
checkUserId = 0


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
    with open(os.path.join(current_path + '/logs', date)) as log:
        textInFile = log.read()
    textInFile = textInFile.split('\n')
    # return textInFile
    return render_template("logsshow.html", linelist=textInFile)


@app.route('/submitchanges', methods=['POST'])
def submitchanges():
    print request.form
    return 'placeholder'

# Loop that calls the Instagram Checkstuff things can be activated from automaticly through time or from the webgui
# TODO Finish all the possible Automated things
# TODO Finish Deadling with All Possible Web gui calls
def loopThread():
    previousCheckTime = time.time()  # set oldcheck time as current when thread starts
    print "placeholder"
    while True:
        current_time = time.time()
        # Automated Things
        if previousCheckTime is not 0:
            if current_time >= previousCheckTime + (interval * 60):
                # Set new check time
                previousCheckTime = time.time()  # Set new time
                print 'Time Check'
                continue
        #Called from WebGui Stuff
        if updateDates:
            print 'Update Dates'

            updateDates = False
        if checkAllNow:
            print 'Check All Now'
            if updateTime:
                previousCheckTime = time.time()
                updateTime = False
            Instagrambot.updateAll()
            checkAllNow = False
            continue
        if checkUser:
            print 'Check User'
            if checkUserId is not 0:
                Instagrambot.updateUser(checkUserId)
                checkUserId = 0  # Reset Id
            else:
                print "User Id is empty"
            checkUser = False
            continue
Instagrambot = threading.Thread

app.run()
