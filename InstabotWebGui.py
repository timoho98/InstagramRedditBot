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
ContinueRunning = True
updateDates = False
checkAllNow = False
updateTime = False
checkUser = False
autoCheck = False
checkUserId = 0

#Stats
LastManualCheck = 'None'

def getLogFiles(dir_='./logs/'):
    filelist = []
    for file in os.listdir(dir_):
        if file.endswith(".log"):
            filelist.append(file)
    return filelist


@app.route('/')
def hello_world():
    return render_template("Index.html")


@app.route('/dashboard')
def dashboard():
    iseverythingdone = False
    global updateDates
    global checkAllNow
    if updateDates is False and checkAllNow is False and checkUser is False:
        iseverythingdone = True
    lastdates = Instagrambot.getListIdDate()
    return render_template("dashboard.html", idlist=Instagrambot.jsonIdData, everythingdone=iseverythingdone, lastdatelist=lastdates, checkUser=checkUser, checkAllNow=checkAllNow, updateDates=updateDates, previouschecktime=previousCheckTime)


@app.route('/status', methods=['POST', 'GET'])
def status():
    iseverythingdone = False
    isCheckUser = False
    idJson = []
    idLastDate = ""
    global updateDates
    global checkAllNow
    if updateDates is False and checkAllNow is False and checkUser is False:
        iseverythingdone = True
    action = str(request.args.get("action"))
    if request.method == 'GET':
        if action is not 'None':
            if action == 'CheckAllNow':
                checkAllNow = True
            elif action == 'Updatedates':
                updateDates = True
            else:
                print 'placeholder'
    if request.method == 'POST':
        isCheckUser = True
        global checkUserId
        checkUserId = Instagrambot.getIdFromName(request.form['name'])
        idJson = Instagrambot.getJsonDict(checkUserId)
        idLastDate = Instagrambot.getLastDate(checkUserId)
        print idLastDate
    namelist = Instagrambot.getListIds()
    lastdates = Instagrambot.getListIdDate()
    return render_template("status.html", everythingdone=iseverythingdone, lastdatelist=lastdates, checkUser=checkUser, checkAllNow=checkAllNow,
                           updateDates=updateDates, previouschecktime=previousCheckTime, namelist=namelist, checkuser=isCheckUser, idJson=idJson, idLastDate=idLastDate)

@app.route('/status/<name>')
def statusname(name):
    return name
@app.route('/checkuser', methods=['POST', 'GET'])
def checkuser():
    idJson = None
    if request.method == 'POST':
        global checkUserId
        global checkUser
        checkUser = True
        checkUserId = Instagrambot.getIdFromName(request.form['name'])
        idJson = Instagrambot.getJsonDict(checkUserId)
        idLastDate = Instagrambot.getLastDate(checkUserId)
    return render_template("checkuser.html", idJson=idJson, idLastdate=idLastDate)


## Below are Test Pages
@app.route('/testrender', methods=['POST', 'GET'])
def testrender():
    global updateDates
    if request.method == 'POST':
        if request.form['thing'] == 'Do Something':
            updateDates = True
            print "Do Something"
        elif request.form['thing'] == 'Do Something Else':
            updateDates = True
            print "Else"
        else:
            print "placeholder"
    return render_template("test.html")

@app.route('/usercheck')
def usercheck():
    return render_template("usercheck.html", idlist=Instagrambot.jsonIdData)

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
    print request.args.get('id')
    return 'User Not Found'


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
    global updateDates
    global checkAllNow
    global checkUser
    global autoCheck
    global previousCheckTime
    previousCheckTime = time.time()  # set oldcheck time as current when thread starts
    print "Started Instagrambot thread"
    while ContinueRunning:
        current_time = time.time()
        # Automated Things
        if autoCheck:
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
            global LastManualCheck
            LastManualCheck = True
            ##Instagrambot.updateAll()
            checkAllNow = False
            continue
        if checkUser:
            print 'Check User'
            global checkUserId
            if checkUserId is not 0:
                ##Instagrambot.updateUser(checkUserId)
                print 'checking:' + checkUserId
                checkUserId = 0  # Reset Id
            else:
                print "User Id is empty"
            checkUser = False
            continue
Instagrambotthread = threading.Thread(target=loopThread)
Instagrambotthread.setDaemon(True)
Instagrambotthread.start()
app.run()
