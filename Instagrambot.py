#!/usr/bin/python
import json, requests, datetime, praw, pprint, ConfigParser, sys, getopt, os
#jexec -u root -n PythonScript sh python /mnt/script/InstagramRedditBot/Instagrambot.py -h
# Get your key/secret from http://instagram.com/developer/
config = ConfigParser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'))
#config.read("config2.ini")
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
currentunixtimestamp = datetime.datetime.utcnow()
updatedjson = []

#file loading
#loading Json from target file
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), TARGET_JSON_FILE)) as Jsonidfile:
    jsoniddata = json.load(Jsonidfile)

r = praw.Reddit(user_agent=REDDIT_USERAGENT)
r.login(REDDIT_USERNAME, REDDIT_PASSWORD)
postsubreddit = praw.objects.Subreddit(reddit_session= r, subreddit_name= REDDIT_SUBREDDIT)

def logstuff (text): #automaticly adds the new like '\n' at the end of every entry
    currentdaymonthyear = str(currentunixtimestamp.year) + "-" + str(currentunixtimestamp.month) + "-" + str(currentunixtimestamp.day)
    #print currentdaymonthyear
    print ("Logged: " + text + " in " + currentdaymonthyear + ".log")
    log = open(currentdaymonthyear + ".log", "a")
    log.write(text + '\n')
    log.close()

def imgurupload (imageurl, title): #uploads image to imgur returns False if fails, params need .jpq url and title
    header = {"Authorization": "Client-ID " + IMGUR_CLIENT_ID}
    data = {'image': imageurl,
            'title': title,
            'key' : IMGUR_CLIENT_SECRET}
    response = requests.post(url = 'https://api.imgur.com/3/upload.json', data = data, headers = header)
    j = json.loads(response.text)
    if j['success']:
        img_url = j['data']['link']
        logstuff("Uploaded Image to " + img_url)
        print(str(img_url))
        return j
    else:
        print j['status']
        print "Failed"
        logstuff("Failed to Upload Image returned with error" + j['status'])
        return False

def checkifidindata (username): #check if username exists in data jsoniddata
    for i in jsoniddata:
        if i['name'] == username:
            return True
    return False

def chooseflair (username): #choose flair based on username returns a html flair id, params needed, username
    for i in jsoniddata:
        if i['name'] == username:
            flairid = i['flairid']
            print flairid
            return flairid

def writetodate (date, username): #write last date to config file (outdated, currently json is setup for write to jsonfile
    config.set('lastdate', username, date)
    logstuff('Updated Last date for:' + username + ' to:' + date)

def writetodatejson (date, username, jsondict): #more updated version of write to date updates json file with data and username
    for j in jsoniddata:
        if j['name'] == username:
            j['lastdate'] = date
            logstuff('Updated last date to ' + str(date) + ' for:' + username)
            return jsondict

def getendoflink(link): #gets the last part of a instagramlink for later uses
    endpart = link.split('/')
    return endpart[4]

def getlistid():
    for id in jsoniddata:
        print id['name']

def getmediaJSON (userid): #Get json of most recent media param Userid dict from json
    mediareturn = requests.get('https://api.instagram.com/v1/users/' + str(userid['userid']) + '/media/recent/?client_id=' + INSTAGRAM_CLIENT_ID)
    logstuff("Starting request at " + str(currentunixtimestamp.year) + "-" + str(currentunixtimestamp.month) + "-" + str(currentunixtimestamp.day) + " of InstaId:" + str(userid['userid']))
    print "Requested from " + str(userid['userid'])
    mediareturnJSON = mediareturn.json()
    return mediareturnJSON

def generatecommenttext(source):
    commentstring = "[Source](" + source  + ")"
    return commentstring
def submittoreddit(url,  linkcaption, source): #post to subreddit, param url, and add comment at the end of submission
    redditsubmissionlink = postsubreddit.submit(title = linkcaption, url = url)
    #TODO add more things to comment
    redditsubmissionlink.add_comment(generatecommenttext(source))
    return redditsubmissionlink

def checkimage (media , idjson): #check if image is later than the lastdate on file, returns a true or false
    Instagram_username = media['user']['username']
    lastdate = idjson['lastdate']
    if int(media['created_time']) > int(lastdate): #check date then check filetype
        print 'Found new media for ' + Instagram_username
        logstuff("Image:" + media['id'] + " created date:" + datetime.datetime.fromtimestamp(int(media['created_time'])).strftime('%Y-%m-%d %H:%M:%S') + " after " + datetime.datetime.fromtimestamp(int(lastdate)).strftime('%Y-%m-%d %H:%M:%S'))
        return True
    else:
        #print media['created_time'] + 'olderthan' + lastdate
        return False

def checktype (imagemedia): #check if json is video or image, returns a 1 if image, returns a 2 if video
    if imagemedia['type'] == 'image':
        return 1
    elif imagemedia['type'] == 'video':
        return 2

def processimage (imagemedia): #process the media given a media json
    Instagram_username = imagemedia['user']['username']
    #gather data from media obj
    imageurl = imagemedia['images']['standard_resolution']['url']
    if imagemedia['caption'] is None:  #check if there is a caption or not
        print "Text/title dne"
        caption = "No Caption"
    else:
        caption = imagemedia['caption']['text']
        print 'Caption:' + caption
    #print str(imagemedia['caption'])
    logstuff("Starting Upload of image " + str(imagemedia['id']))
    imgurjson = imgurupload(imageurl, caption)
    if imgurjson['success']:
        submittedlink = submittoreddit(url = imgurjson['data']['link'], linkcaption = caption, source= imagemedia['link'])
        #TODO use check if id in data then get flair id
        r.select_flair(item = submittedlink, flair_template_id= 'd1e51b54-5fb1-11e4-a579-12313b0e5086') #flair_template_id= chooseflair(username = Instagram_username, iddata = jsoniddata))
        logstuff("Submitted Link")
    #writetodate(date = lastdate, username= Instagram_username)
    logstuff("")

def processvideo(imagemedia): #do processing for video
    videourl = imagemedia['link']
    print "placeholder"

def updatewithid (iddict): #check instagram for new pictures with particular id
    mediaJSON = getmediaJSON(iddict)
    print "Checking id:" + iddict['name']
    print "Last Date:" + str(iddict['lastdate'])
    #print "Print mediajson" + str(mediaJSON)
    for m in mediaJSON['data']:
        if checkimage(media = m, idjson = iddict):
            if checktype(m) == 1:
                processimage(imagemedia= m)
            elif checktype(m) == 2:
                processvideo(m)
            lastpartoflink = getendoflink(m['link'])
            global updatedjson
            updatedjson= writetodatejson(date = m['created_time'], username= m['user']['username'], jsondict= jsoniddata) #update json in program have not written to file yet

arguments = sys.argv[1:] #get arguments after the command run
try:
    opts, args = getopt.getopt(arguments, 'tu:ch', ['test', 'user=', 'check', 'help'])
except getopt.GetoptError:
    print ('arg not recongnized')
for opt, arg in opts:
    if opt in ('-t, --test'):
        print 'test'
    elif opt in ('-u', '--user'):
        if checkifidindata(username=arg):
            for id in jsoniddata: #parse through list to find the id there is probably a better way to do this or organize data better but idk what it is
                if id['name'] == str(arg):
                    updatewithid(id)
        else:
            print "error " + arg + " does not exist in config"
    elif opt in ('-c', '--check'):
       for ids in jsoniddata:
            print "print id" + ids
            updatewithid(ids)
    elif opt in ('-h', '--help'):
        print 'The current commands are:'
        print '-user, - u: (Username) update a specific id'
        print '-check, -c :basicly go through all ids and check'

#write with updated json
#updatedjson = writetodatejson(date = 230492, username= 'test', jsondict= jsoniddata)
"""
with open(TARGET_JSON_FILE, 'w') as newjsonfile: #part where we write to file
    json.dump(updatedjson, newjsonfile, indent = 4, separators=(', ', ': '))
"""


