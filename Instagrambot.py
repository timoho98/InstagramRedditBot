#!/usr/bin/python
import json, requests, datetime, praw, ConfigParser, sys, getopt, os, copy
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
currentunixtimestamp = datetime.datetime.utcnow()

#TODO Video processing
#TODO Error Handle for instagram and Reddit

r = praw.Reddit(user_agent=REDDIT_USERAGENT)
r.login(REDDIT_USERNAME, REDDIT_PASSWORD)
postsubreddit = praw.objects.Subreddit(reddit_session= r, subreddit_name= REDDIT_SUBREDDIT)
#file loading
#loading Json from target file
#print os.path.join(os.path.abspath(os.path.dirname(__file__)), TARGET_JSON_FILE)
with open(os.path.join(current_path, TARGET_JSON_FILE)) as Jsonidfile:
    jsoniddata = json.load(Jsonidfile)
updatedjson = copy.deepcopy(jsoniddata)
#submissionobj = postsubreddit.get_flair_choices(link = 'http://redd.it/2ocgcv')
#print submissionobj

#TODO Change how month day year hour and min are get to datetime ex #datetime.datetime.fromtimestamp(int(media['created_time'])).strftime('%Y-%m-%d %H:%M:%S')
def logstuff (text): #automaticly adds the new like '\n' at the end of every entry
    currenttime = str(currentunixtimestamp.hour) + ":" + str(currentunixtimestamp.minute)
    currentdaymonthyear = str(currentunixtimestamp.year) + "-" + str(currentunixtimestamp.month) + "-" + str(currentunixtimestamp.day)
    #print currentdaymonthyear
    print ("Logged: " + text + " in " + currentdaymonthyear + ".log at " + currenttime)
    log = open(os.path.join(current_path, currentdaymonthyear + ".log"), "ab")
    log.write(currentdaymonthyear + " " + currenttime + ": " +text + '\n')
    log.close()

#uploads image to imgur returns False if fails, params need .jpq url and title
def imgurupload (imageurl, title):
    header = {"Authorization": "Client-ID " + IMGUR_CLIENT_ID}
    data = {'image': imageurl,
            'title': title,
            'key' : IMGUR_CLIENT_SECRET}
    response = requests.post(url = 'https://api.imgur.com/3/upload.json', data = data, headers = header)
    j = json.loads(response.text)
    if j['success']:
        img_url = j['data']['link']
        logstuff("Uploaded Image to " + img_url)
        return j
    else:
        print j['status']
        print "Failed"
        logstuff("Failed to Upload Image returned with error" + j['status'])
        return False

#check if username exists in data jsoniddata
def checkifidindata (username):
    for i in jsoniddata:
        if i['name'] == username:
            return True
    return False

#choose flair based on username returns a html flair id, params needed, username
def chooseflair (username):
    for i in jsoniddata:
        if i['name'] == username:
            flairid = i['flairid']
            return flairid

#OUTDATED
#write last date to config file (outdated, currently json is setup for write to jsonfile
def writetodate (date, username):
    config.set('lastdate', username, date)
    logstuff('Updated Last-date for:' + username + ' to:' + date)

#more updated version of write to date updates json file with data and username
def writetodatejson (date, username):
    global updatedjson #updates global var
    for j in updatedjson:
        if j['name'] == username:
            if j['lastdate'] < date: #In case images are not analyzed in chronological order (Most likely wont) and there are multiple images in one pass
                j['lastdate'] = date
                logstuff('Updated last date to ' + str(date) + ' for:' + username)

#gets the last part of a instagramlink for later uses
def getendoflink(link):
    endpart = link.split('/')
    return endpart[4]

#List Ids that exist in the json file
def getlistid():
    idstring = ''
    for id in jsoniddata:
        idstring += id['name']
        idstring += '\n'
    return idstring

#list ids as well as last dates
def getlistiddate():
    iddatestring = []
    for id in jsoniddata:
        iddatestring.append(id['name'] + ' - ' + str(datetime.datetime.fromtimestamp(int(id['lastdate']))) + '\n')
    return iddatestring

#Get json of most recent media param Userid dict from json
def getmediaJSON (userid):
    mediareturn = requests.get('https://api.instagram.com/v1/users/' + str(userid['userid']) + '/media/recent/?client_id=' + INSTAGRAM_CLIENT_ID)
    logstuff("Request JSON of InstaId:" + str(userid['name']) + " User Id:" +str(userid['userid']))
    #print "Requested from " + str(userid['userid'])
    mediareturnJSON = mediareturn.json()
    return mediareturnJSON

#Generates Text for comment
def generatecommenttext(source):
    commentstring = "[Source](" + source  + ")" #format source text
    return commentstring
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
def submittoreddit(url,  linkcaption, source):
    redditsubmission = postsubreddit.submit(title = linkcaption, url = url)
    #TODO add more things to comment
    logstuff("Submitted Link to Reddit at " + redditsubmission.short_link)
    redditsubmission.add_comment(generatecommenttext(source))
    return redditsubmission

#check if image is later than the lastdate on file, returns a true or false
def checkimage (media , idjson):
    Instagram_username = media['user']['username']
    lastdate = idjson['lastdate']
    if int(media['created_time']) > int(lastdate): #check date then check filetype
        logstuff("New Media for " + Instagram_username +" found at :" + media['link'] + " created date:" + datetime.datetime.fromtimestamp(int(media['created_time'])).strftime('%Y-%m-%d %H:%M:%S') + " after Last-Date:" + datetime.datetime.fromtimestamp(int(lastdate)).strftime('%Y-%m-%d %H:%M:%S'))
        return True
    else:
        #print media['link'] +" " +media['created_time'] + ' olderthan' + lastdate
        return False

#OUTDATED USELESS
#check if json is video or image, returns a 1 if image, returns a 2 if video
def checktype (imagemedia):
    if imagemedia['type'] == 'image':
        return 1
    elif imagemedia['type'] == 'video':
        return 2

#process the media given a media json
def processimage (imagejson):
    Instagram_username = imagejson['user']['username']
    #gather data from media obj
    imageurl = imagejson['images']['standard_resolution']['url']
    if imagejson['caption'] is None:  #check if there is a caption or not
        print "Text/title dne"
        caption = "No Caption"
    else:
        caption = imagejson['caption']['text']
        #print 'Caption:' + caption #Removed because cant print special chars
    #print str(imagemedia['caption'])
    logstuff("Starting Upload of image " + str(imagejson['link']))
    imgurjson = imgurupload(imageurl, caption)
    if imgurjson['success']:
        submittedlink = submittoreddit(url = imgurjson['data']['link'], linkcaption = caption, source= imagejson['link'])
        r.select_flair(item = submittedlink, flair_template_id= chooseflair(username = Instagram_username))
        logstuff("Selected flair for " + Instagram_username)
        #flair_template_id= 'd1e51b54-5fb1-11e4-a579-12313b0e5086') #flair_template_id= chooseflair(username = Instagram_username))
    logstuff("Finished Processing image for " + Instagram_username + " Imageid: " + imagejson['id'])

#do processing for video
def processvideo(videojson):
    Instagram_username = videojson['user']['username']
    videourl = videojson['videos']['standard_resolution']['url']
    if videojson['caption'] is None: #check if there is a caption or not
        print "Text/title dne"
        caption = "No Caption"
    else:
        caption = videojson['caption']['text']
    submittedlink = submittoreddit(url = videourl, linkcaption= caption, source= videojson['link'])
    r.select_flair(item = submittedlink, flair_template_id= chooseflair(username = Instagram_username))
    logstuff("Selected flair for " + Instagram_username)
    logstuff("Finished Processing video for " + Instagram_username + " Videoid:" + videojson['id'])

#check instagram for new pictures with particular id
def updatewithid (iddict):
    mediaJSON = getmediaJSON(iddict)
    #TODO Change to logstuff
    print "Checking id:" + iddict['name']
    print "Last Date:" + str(iddict['lastdate'])
    #print "Print mediajson" + str(mediaJSON)
    for m in mediaJSON['data']:
        if checkimage(media = m, idjson = iddict):
            if m['type'] == 'image':
                processimage(imagemedia= m)
            elif m['type'] == 'video':
                processvideo(m)
            lastpartoflink = getendoflink(m['link'])
            writetodatejson(date = m['created_time'], username= m['user']['username'])

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
            if checkifidindata(username=arg):
                for id in jsoniddata: #parse through list to find the id there is probably a better way to do this or organize data better but idk what it is
                    if id['name'] == str(arg):
                        updatewithid(id)
                with open(os.path.join(current_path, TARGET_JSON_FILE), 'wb') as newjsonfile: #part where we write to file
                    json.dump(updatedjson, newjsonfile, indent = 4, separators=(', ', ': '))
                logstuff("Updated Jsonfile")
            else:
                print "error " + arg + " does not exist in config"
        elif opt in ('-c', '--check'):
            logstuff("Running Check Command")
            #logstuff("Running Check command at " + currentunixtimestamp.hour + ":" + currentunixtimestamp.minute + " on " + currentunixtimestamp.month + "-" + currentunixtimestamp.day)
            for ids in jsoniddata:
                updatewithid(ids)
            with open(os.path.join(current_path, TARGET_JSON_FILE), 'wb') as newjsonfile: #part where we write to file
                json.dump(updatedjson, newjsonfile, indent = 4, separators=(', ', ': '))
            logstuff("Updated Jsonfile")
        elif opt in ('-h', '--help'):
            print 'The current commands are:'
            print '--user, -u: Params: (Username), update a specific id'
            print '--check, -c: No Params: basically go through all ids and check'
        elif opt in ('-l', 'list'):
            print getlistid()
        else:
            print 'No command detected, please add -h or --help at the end of console command to bring up a list of commands'



