#!/usr/bin/python
import json, requests, datetime, praw, ConfigParser, sys, getopt, os, copy, time
#jexec -u root -n PythonScript sh python /mnt/script/InstagramRedditBot/Instagrambot.py -h
current_path = os.path.abspath(os.path.dirname(__file__))
# Get your key/secret from http://instagram.com/developer/
config = ConfigParser.ConfigParser()
config.read(os.path.join(current_path, 'config.ini'))
INSTAGRAM_CLIENT_ID = config.get("instagram", "clientid")
INSTAGRAM_CLIENT_SECRET = config.get("instagram", "clientsecret")
IMGUR_CLIENT_ID = config.get("imgur", "clientid")
IMGUR_CLIENT_SECRET = config.get("imgur", "clientsecret")
REDDIT_USERAGENT = config.get("reddit", "userAgent")
REDDIT_USERNAME = config.get("reddit", "username")
REDDIT_PASSWORD = config.get("reddit", "password")
REDDIT_SUBREDDIT = config.get("reddit", "subreddit")
TARGET_JSON_FILE = config.get("File", "Name")
img_url = ''
caption = ''
currentunixtimestamp = time.time()
print currentunixtimestamp
#TODO Video processing
#TODO Error Handle for instagram and Reddit

r = praw.Reddit(user_agent=REDDIT_USERAGENT)
r.login(REDDIT_USERNAME, REDDIT_PASSWORD)
postsubreddit = praw.objects.Subreddit(reddit_session= r, subreddit_name= REDDIT_SUBREDDIT)
#file loading
#loading Json from target file
#print os.path.join(os.path.abspath(os.path.dirname(__file__)), TARGET_JSON_FILE)
with open(os.path.join(current_path, TARGET_JSON_FILE)) as jsonIdFile:
    jsonIdData = json.load(jsonIdFile)
updatedJson = copy.deepcopy(jsonIdData)
#submissionobj = postsubreddit.get_flair_choices(link = 'http://redd.it/2ocgcv')
#print submissionobj

def logStuff (text): #automaticly adds the new like '\n' at the end of every entry
    time = datetime.datetime.fromtimestamp(currentunixtimestamp).strftime('%H:%M:%S')
    date = datetime.datetime.fromtimestamp(currentunixtimestamp).strftime('%Y-%m-%d')
    print ("Logged: '" + text + "' in " + date + ".log at " + time)
    log = open(os.path.join(current_path, date + ".log"), "ab")
    log.write(date + " " + time + ": " +text + '\n')
    log.close()

#uploads image to imgur returns False if fails, params need .jpq url and title
def imgurUpload (imageUrl, title):
    header = {"Authorization": "Client-ID " + IMGUR_CLIENT_ID}
    data = {'image': imageUrl,
            'title': title,
            'key' : IMGUR_CLIENT_SECRET}
    response = requests.post(url = 'https://api.imgur.com/3/upload.json', data = data, headers = header)
    j = json.loads(response.text)
    if j['success']:
        img_url = j['data']['link']
        logStuff("Uploaded Image to " + img_url)
        return j
    else:
        print j['status']
        print "Failed"
        logStuff("Failed to Upload Image returned with error" + j['status'])
        return False

#check if username exists in data jsoniddata
def checkIfNameInData (username):
    for i in jsonIdData:
        if i['name'] == username:
            return True
    return False

#check if id exists in data jsoniddata
def checkIdInData (userid):
    for i in jsonIdData:
        if i['id'] == userid:
            return True
    return False

#choose flair based on username returns a html flair id, params needed, username
def chooseFlair (username):
    for i in jsonIdData:
        if i['name'] == username:
            flairid = i['flairid']
            return flairid

#more updated version of write to date updates json file with data and username
def writeToDateJson (date, username):
    global updatedJson #updates global var
    for j in updatedJson:
        if j['name'] == username:
            if j['lastdate'] < date: #In case images are not analyzed in chronological order (Most likely wont) and there are multiple images in one pass
                j['lastdate'] = date
                logStuff('Updated last date to ' + str(date) + ' for:' + username)

#gets the last part of a instagramlink for later uses
def getEndOfLink(link):
    endpart = link.split('/')
    return endpart[4]

#List Ids that exist in the json file
def getListIds():
    idString = ''
    for id in jsonIdData:
        idString += id['name']
        idString += '\n'
    return idString

#Get id from name input
def getIdFromName(name):
    for i in jsonIdData:
        if i['name'] == name:
            return i['userid']
#Get Json Dict from id
def getJsonDict (id):
    if type(id) is int:
        for i in jsonIdData:
            if i['id'] == id:
                return i
    if type(id) is str:
        for i in jsonIdData:
            if i['name'] == id:
                return i
#list ids as well as last dates
def getListIdDate():
    idDateString = []
    for id in jsonIdData:
        idDateString.append(id['name'] + ' - ' + str(datetime.datetime.fromtimestamp(int(id['lastdate']))) + '\n')
    return idDateString

#Get json of most recent media param Userid dict from json
def getMediaJSON (userid):
    mediaReturn = requests.get('https://api.instagram.com/v1/users/' + str(userid['userid']) + '/media/recent/?client_id=' + INSTAGRAM_CLIENT_ID)
    logStuff("Request JSON of InstaId:" + str(userid['name']) + " User Id:" +str(userid['userid']))
    #print "Requested from " + str(userid['userid'])
    mediaReturnJSON = mediaReturn.json()
    return mediaReturnJSON

#Generates Text for comment
def generateCommentText(source):
    commentString = "[Source](" + source  + ")" #format source text
    return commentString
'''
Expected output for comment
Source #as link
Created Time (Unix Epoch Time
Filter:
Tags
if video thumbnail
allow for true false if should be enabled
'''

#post to subreddit, param url, and add comment at the end of submission
def submitToReddit(url,  linkCaption, source):
    redditSubmission = postsubreddit.submit(title = linkCaption, url = url)
    #TODO add more things to comment
    logStuff("Submitted Link to Reddit at " + redditSubmission.short_link)
    redditSubmission.add_comment(generateCommentText(source))
    return redditSubmission

#check if image is later than the lastdate on file, returns a true or false
def checkImage (media , idJson):
    Instagram_Username = media['user']['username']
    lastDate = idJson['lastdate']
    if int(media['created_time']) > int(lastDate): #check date then check filetype
        logStuff("New Media for " + Instagram_Username +" found at :" + media['link'] + " created date:" + datetime.datetime.fromtimestamp(int(media['created_time'])).strftime('%Y-%m-%d %H:%M:%S') + " after Last-Date:" + datetime.datetime.fromtimestamp(int(lastDate)).strftime('%Y-%m-%d %H:%M:%S'))
        return True
    else:
        #print media['link'] +" " +media['created_time'] + ' olderthan' + lastdate
        return False

#OUTDATED USELESS
#check if json is video or image, returns a 1 if image, returns a 2 if video
def checkType (imageMedia):
    if imageMedia['type'] == 'image':
        return 1
    elif imageMedia['type'] == 'video':
        return 2

#process the media given a media json
def processImage (imageJson):
    instagram_Username = imageJson['user']['username']
    #gather data from media obj
    imageurl = imageJson['images']['standard_resolution']['url']
    if imageJson['caption'] is None:  #check if there is a caption or not
        print "Text/title dne"
        caption = "No Caption"
    else:
        caption = imageJson['caption']['text']
        #print 'Caption:' + caption #Removed because cant print special chars
    #print str(imagemedia['caption'])
    logStuff("Starting Upload of image " + str(imageJson['link']))
    imgurjson = imgurUpload(imageurl, caption)
    if imgurjson['success']:
        submittedLink = submitToReddit(url = imgurjson['data']['link'], linkCaption = caption, source= imageJson['link'])
        r.select_flair(item = submittedLink, flair_template_id= chooseFlair(username = instagram_Username))
        logStuff("Selected flair for " + instagram_Username)
        #flair_template_id= 'd1e51b54-5fb1-11e4-a579-12313b0e5086') #flair_template_id= chooseflair(username = Instagram_username))
    logStuff("Finished Processing image for " + instagram_Username + " Imageid: " + imageJson['id'])

#do processing for video
def processVideo(videoJson):
    instagram_Username = videoJson['user']['username']
    videoUrl = videoJson['videos']['standard_resolution']['url']
    if videoJson['caption'] is None: #check if there is a caption or not
        print "Text/title dne"
        caption = "No Caption"
    else:
        caption = videoJson['caption']['text']
    submittedLink = submitToReddit(url = videoUrl, linkCaption= caption, source= videoJson['link'])
    r.select_flair(item = submittedLink, flair_template_id= chooseFlair(username = instagram_Username))
    logStuff("Selected flair for " + instagram_Username)
    logStuff("Finished Processing video for " + instagram_Username + " Videoid:" + videoJson['id'])

#check instagram for new pictures with particular id
def updateWithId (iddict):
    mediaJSON = getMediaJSON(iddict)
    #TODO Change to logstuff
    print "Checking id:" + iddict['name']
    print "Last Date:" + str(iddict['lastdate'])
    #print "Print mediajson" + str(mediaJSON)
    for m in mediaJSON['data']:
        if checkImage(media = m, idJson = iddict):
            if m['type'] == 'image':
                processImage(m)
            elif m['type'] == 'video':
                processVideo(m)
            lastpartoflink = getEndOfLink(m['link'])
            writeToDateJson(date = m['created_time'], username=m['user']['username'])

if __name__ == "__main__": #only runs if not loaded as a module
    arguments = sys.argv[1:] #get arguments after the command run
    try:
        opts, args = getopt.getopt(arguments, 'tu:chl', ['test', 'user=', 'check', 'help', 'list'])
    except getopt.GetoptError:
        print ('arg not recongnized')
    for opt, arg in opts:
        if opt in ('-t, --test'):
            print 'test'
        elif opt in ('-u', '--user'):
            if checkIfNameInData(username=arg):
                for id in jsonIdData: #parse through list to find the id there is probably a better way to do this or organize data better but idk what it is
                    if id['name'] == str(arg):
                        updateWithId(id)
                with open(os.path.join(current_path, TARGET_JSON_FILE), 'wb') as newjsonfile: #part where we write to file
                    json.dump(updatedJson, newjsonfile, indent = 4, separators=(', ', ': '))
                logStuff("Updated Jsonfile")
            else:
                print "error " + arg + " does not exist in config"
        elif opt in ('-c', '--check'):
            logStuff("Running Check Command")
            #logstuff("Running Check command at " + currentunixtimestamp.hour + ":" + currentunixtimestamp.minute + " on " + currentunixtimestamp.month + "-" + currentunixtimestamp.day)
            for ids in jsonIdData:
                updateWithId(ids)
            with open(os.path.join(current_path, TARGET_JSON_FILE), 'wb') as newjsonfile: #part where we write to file
                json.dump(updatedJson, newjsonfile, indent = 4, separators=(', ', ': '))
            logStuff("Updated Jsonfile")
        elif opt in ('-h', '--help'):
            print 'The current commands are:'
            print '--user, -u: Params: (Username), update a specific id'
            print '--check, -c: No Params: basically go through all ids and check'
        elif opt in ('-l', 'list'):
            print getListIds()
        else:
            print 'No command detected, please add -h or --help at the end of console command to bring up a list of commands'