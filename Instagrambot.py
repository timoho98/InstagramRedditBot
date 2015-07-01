#!/usr/bin/python
import json
import requests
import datetime
import praw
import ConfigParser
import sys
import getopt
import os
import copy
import time
# jexec -u root -n PythonScript sh python /mnt/script/InstagramRedditBot/Instagrambot.py -h
current_path = os.path.abspath(os.path.dirname(__file__))
# Get your key/secret from http://instagram.com/developer/
config = ConfigParser.ConfigParser()
config.read(os.path.join(current_path, 'config.ini'))
INSTAGRAM_CLIENT_ID = config.get("Instagram", "Clientid")
INSTAGRAM_CLIENT_SECRET = config.get("Instagram", "ClientSecret")
IMGUR_CLIENT_ID = config.get("Imgur", "Clientid")
IMGUR_CLIENT_SECRET = config.get("Imgur", "ClientSecret")
REDDIT_USERAGENT = config.get("Reddit", "UserAgent")
REDDIT_USERNAME = config.get("Reddit", "Username")
REDDIT_PASSWORD = config.get("Reddit", "Password")
REDDIT_SUBREDDIT = config.get("Reddit", "Subreddit")
TARGET_JSON_FILE = config.get("ScriptSettings", "JSONFileName")
# TODO Video processing (kinda done?)
# TODO Error Handling for instagram and Reddit

r = praw.Reddit(user_agent=REDDIT_USERAGENT)
r.login(REDDIT_USERNAME, REDDIT_PASSWORD)
postsubreddit = praw.objects.Subreddit(reddit_session=r, subreddit_name=REDDIT_SUBREDDIT)
# file loading
# loading Json from target file
# print os.path.join(os.path.abspath(os.path.dirname(__file__)), TARGET_JSON_FILE)
with open(os.path.join(current_path, TARGET_JSON_FILE)) as jsonIdFile:
    jsonIdData = json.load(jsonIdFile)

# Copy a version of json
# Use this copy to make changes to JSON file
# jsonIdData is used as reference to old data so updatedJson can be changed without waiting for program to end
updatedJson = copy.deepcopy(jsonIdData)

# Update Functions
# Check instagram for new pictures with particular id
def updateWithId(iddict):
    mediaJSON = getMediaJSON(iddict)
    # TODO Add to logstuff
    print "Checking user:" + iddict['name']
    print "Last Date:" + str(iddict['lastdate'])
    # print "Print mediajson " + str(mediaJSON)
    for m in mediaJSON['data']:
        if checkImage(media=m, idJson=iddict):
            if m['type'] == 'image':
                processImage(m)
            elif m['type'] == 'video':
                processVideo(m)
            # lastpartoflink = getEndOfLink(m['link'])
            writeToDateJson(date=int(m['created_time']), username=m['user']['username'])


# Update the JSON file with current updatedjson list
def updateJSON():
    with open(os.path.join(current_path, TARGET_JSON_FILE), 'wb') as newjsonfile:  # Part where we write to file
        json.dump(updatedJson, newjsonfile, indent=4, separators=(', ', ': ')) #formating
    logStuff("Updated Jsonfile")
    updateJSONfromfile()

# Update lastpost dates to current dates
def updateLastdate(user='all'):
    if user == 'all':
        logStuff('Updating lastDates for all users')
        for ids in updatedJson:
            userMediaJSON = getMediaJSON(ids)
            for media in userMediaJSON['data']:
                if ids['lastdate'] < int(media['created_time']):
                    writeToDateJson(date=int(media['created_time']), username=media['user']['username'])
    else:
        if checkIfNameInData(user):
            logStuff('Updating lastDates for ' + user)
            userJSON = getJsonDict(user, getFromUpdatedJSON=True)
            userMediaJSON = getMediaJSON(userJSON)
            for media in userMediaJSON['data']:
                if userJSON['lastdate'] < media['created_time']:
                    writeToDateJson(date=int(media['created_time']), username=media['user']['username'])


def updateJSONfromfile():
    global jsonIdData
    with open(os.path.join(current_path, TARGET_JSON_FILE)) as jsonIdFile:
        jsonIdData = json.load(jsonIdFile)
    print 'Updated JSON from file'


# Check all ids in jsonID
def updateAll():
    for ids in jsonIdData:
        updateWithId(ids)


# Check Specific user, looks for user in json
def updateUser(user):
    if checkIfNameInData(user):
        for id in jsonIdData:  # Parse through list to find the id there is probably a better way to do this or organize data better but idk what it is
            if id['name'] == str(user):
                updateWithId(id)


# Check Functions
# check if username exists in data jsoniddata
def checkIfNameInData(username):
    for i in jsonIdData:
        if i['name'] == username:
            return True
    print 'ERROR ' + username + ' does not exist in JSON file'
    return False


# check if id exists in data jsoniddata
def checkIdInData(userId):
    for i in jsonIdData:
        if i['id'] == userId:
            return True
    return False


# Check if image is later than the lastdate on file, returns a true or false
def checkImage(media, idJson):
    instagramUsername = media['user']['username']
    lastDate = idJson['lastdate']
    createdTime = int(media['created_time'])
    if createdTime > lastDate:  # check date then check filetype
        logStuff("New Media for " + instagramUsername + " found at :" + media[
            'link'] + " created date:" + datetime.datetime.utcfromtimestamp(createdTime).strftime(
            '%Y-%m-%d %H:%M:%S') + " after Last-Date:" + datetime.datetime.utcfromtimestamp(lastDate).strftime(
            '%Y-%m-%d %H:%M:%S'))
        return True
    else:
        # print media['link'] +" " +media['created_time'] + ' olderthan' + lastdate
        return False


# OUTDATED USELESS
# check if json is video or image, returns a 1 if image, returns a 2 if video
def checkType(imageMedia):
    if imageMedia['type'] == 'image':
        return 1
    elif imageMedia['type'] == 'video':
        return 2


# Get Functions
# Gets the last part of a instagramlink for later uses
def getEndOfLink(link):
    endpart = link.split('/')
    return endpart[4]


# List Ids that exist in the json file
def getListIds():
    idList = []
    for id in jsonIdData:
        idList.append(id['name'])
    return idList


# Get id from name input
def getIdFromName(name):
    for i in jsonIdData:
        if i['name'] == name:
            return i['userid']
    return 'Name:' + name + 'does not exist in JSON'


# Get Json Dict from id or name
def getJsonDict(id, getFromUpdatedJSON = False):
    if getFromUpdatedJSON == True:
        jsonList = updatedJson
    else:
        jsonList = jsonIdData
    if type(id) is int:
        for i in jsonList:
            if i['userid'] == id:
                return i
    if type(id) is str:
        for i in jsonList:
            if i['name'] == id:
                return i


# List ids as well as last dates
def getListIdDate():
    idDateString = []
    for id_ in jsonIdData:
        idDateString.append(id_['name'] + ' - ' + str(datetime.datetime.utcfromtimestamp(id_['lastdate'])))
    return idDateString

# Get LastDate from Id
def getLastDate(id, getFromUpdatedJSON = False):
    idJson = getJsonDict(id, getFromUpdatedJSON)
    return str(datetime.datetime.utcfromtimestamp(idJson['lastdate']))

# Instagram Related Functions
# Get json of most recent media param Userid dict from json
def getMediaJSON(userId):
    mediaReturn = requests.get('https://api.instagram.com/v1/users/' + str(userId['userid']) + '/media/recent/?client_id=' + INSTAGRAM_CLIENT_ID)
    logStuff("Request JSON of InstaId:" + str(userId['name']) + " User Id:" + str(userId['userid']))
    mediaReturnJSON = mediaReturn.json()
    return mediaReturnJSON


# process the media given a media json
def processImage(imageJson):
    instagramUsername = imageJson['user']['username']
    # Gather data from media obj
    imageUrl = imageJson['images']['standard_resolution']['url']
    if imageJson['caption'] is None:  # Check if there is a caption or not
        print "Text/title dne"
        caption = "No Caption"
    else:
        caption = imageJson['caption']['text']
        # print 'Caption:' + caption #Removed because cant print special chars
    # print str(imagemedia['caption'])
    logStuff("Starting Upload of image " + str(imageJson['link']))
    imgurjson = imgurUpload(imageUrl, caption)
    if imgurjson['success']:
        # Check if caption is greater than 300 char
        if len(imageJson['caption']['text']) > 300:
            caption = "Caption too long posted in comments"
            commentToLong = True
        else:
            commentToLong = False
        commentstring = generateCommentText(caption=caption, mediaJson=imageJson, tooLong=commentToLong)
        submittedLink = submitToReddit(url=imgurjson['data']['link'], linkCaption=caption, commentString=commentstring)
        userDict = getJsonDict(str(instagramUsername))
        if userDict['flairid'] == 'None':
            print "No flair selected"
        else:
            r.select_flair(item=submittedLink, flair_template_id=chooseFlair(username=instagramUsername))
            logStuff("Selected flair for " + instagramUsername)
        # flair_template_id= 'd1e51b54-5fb1-11e4-a579-12313b0e5086') #flair_template_id= chooseflair(username = Instagram_username))
    logStuff("Finished Processing image for " + instagramUsername + " Imageid: " + imageJson['id'])


# Do processing for video
def processVideo(videoJson):
    instagramUsername = videoJson['user']['username']
    videoUrl = videoJson['videos']['standard_resolution']['url']
    if videoJson['caption'] is None:  # Check if there is a caption or not
        print "Text/title dne"
        caption = "No Caption"
    else:
        caption = videoJson['caption']['text']
    if len(videoJson['caption']['text']) > 300:
        caption = "Caption too long posted in comments"
        commentToLong = True
    else:
        commentToLong = False
    commentstring = generateCommentText(caption=caption, mediaJson=videoJson, tooLong=commentToLong)
    submittedLink = submitToReddit(url=videoUrl, linkCaption=caption, commentString=commentstring)
    # TODO link already submitted error
    userDict = getJsonDict(str(instagramUsername))
    if userDict['flairid'] == 'None':
        print "No flair selected"
    else:
        r.select_flair(item=submittedLink, flair_template_id=chooseFlair(username=instagramUsername))
        logStuff("Selected flair for " + instagramUsername)
    logStuff("Finished Processing video for " + instagramUsername + " Videoid:" + videoJson['id'])


# Imgur Related Functions
# uploads image to imgur returns False if fails, params need .jpq url and title
def imgurUpload(imageUrl, title):
    header = {"Authorization": "Client-ID " + IMGUR_CLIENT_ID}
    data = {'image': imageUrl,
            'title': title,
            'key': IMGUR_CLIENT_SECRET}
    response = requests.post(url='https://api.imgur.com/3/upload.json', data=data, headers=header)
    j = json.loads(response.text)
    if j['success']:
        img_url = j['data']['link']
        logStuff("Uploaded Image to " + img_url)
        return j
    else:
        print j['status']
        print "Failed"
        logStuff("Failed to Upload Image returned with error " + str(j['status']))
        return j


# Reddit Related Functions
# choose flair based on username returns a html flair id, params needed, username
def chooseFlair(username):
    for i in jsonIdData:
        if i['name'] == username:
            flairid = i['flairid']
            return flairid


# TODO add caption to comment if caption too long
# Generates Text for comment
def generateCommentText(mediaJson, caption=None, tooLong = False):
    # Source
    commentString = "[Source](" + mediaJson['link'] + ")"  # format source text
    # If caption too long to fit into title
    if tooLong:
        commentString += "\n\n" + "Caption: " + caption + ""
    # Tags
    if len(mediaJson['tags']) is not 0:
        commentString += "\n\n Tags:"
        for tag in mediaJson['tags']:
            commentString += tag + ", "
    else:
        commentString += "\n\n No Tags"
    # Location
    if mediaJson['location'] is not None:
        commentString += "\n\n Location:"
        commentString += "\n\n Latitude: " + str(mediaJson['location']['latitude']) + " Longitude: " + str(mediaJson['location']['longitude'])
        if 'street_adress' in mediaJson['location']:
            commentString += "\n\n Street Adress: " + mediaJson['location']['street_adress']
        if 'name' in mediaJson['location']:
            commentString += "\n\n Name: " + mediaJson['location']['name']
    else:
        commentString += "\n\n No Location Listed"
    # Users in Photo
    if len(mediaJson['users_in_photo']) is not 0:
        commentString += "\n\n Users in photo:"
        for users in mediaJson['users_in_photo']:
            commentString += "\n\n" + users['user']['full_name'] + " Username: " + users['user']['username']
            commentString += "\n\n [Profile Link](" + "https://instagram.com/" + users['user']['username'] + ")"
            commentString += "\n\n [Profile Picture](" + users['user']['profile_picture'] + ")"
    else:
        commentString += "\n\n No Users Tagged in Photo"
    # Filters
    commentString += "\n\n Filters: " + mediaJson['filter']
    # Created Time
    commentString += "\n\n Created Time(UTC): " + str(datetime.datetime.utcfromtimestamp(int(mediaJson['created_time'])))
    if mediaJson['type'] == 'video':
        commentString += "\n\n [Video Thumbnail](" + mediaJson['images']['standard_resolution']['url'] + ")"
    return commentString


'''
Expected output for comment
Source as link
Created Time (Unix Epoch Time)
Filter:
Tags
if video thumbnail
allow for true false if should be enabled
'''


# Post to subreddit, param url, and add comment at the end of submission
def submitToReddit(url, linkCaption, commentString):
    redditSubmission = postsubreddit.submit(title=linkCaption, url=url)
    # TODO add more things to comment
    logStuff("Submitted Link to Reddit at " + redditSubmission.short_link)
    redditSubmission.add_comment(commentString)
    return redditSubmission


# automaticly adds the new like '\n' at the end of every entry
def logStuff(text):
    time_ = datetime.datetime.utcfromtimestamp(time.time()).strftime('%H:%M:%S')
    date = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d')
    print ("Logged: '" + text + "' in " + date + ".log at " + time_)
    log = open(os.path.join(current_path + '\\logs', date + ".log"), "ab")
    log.write(date + " " + time_ + ": " + text + '\n')
    log.close()


# more updated version of write to date updates json file with data and username
def writeToDateJson(date, username):
    if type(date) is int:
        global updatedJson  # updates global var
        for j in updatedJson:
            # Make sure you actually write the 'LastDate' as media does not process in chronological order
            # TODO attempt to make it chornological
            if j['name'] == username:
                if j['lastdate'] < date:
                    j['lastdate'] = date
                    logStuff('Updated last date to ' + str(date) + ' for:' + username)
    else:
        print 'Date provided to writeToDateJson not a int'


if __name__ == "__main__":  # Only runs if not loaded as a module
    arguments = sys.argv[1:]  # Get arguments after the command run
    if len(arguments) < 1:
        while True:
            print 'Running in Console, quit to quit'
            userinput = raw_input("Enter a Command")
            userinput = userinput.split(" ")
            if userinput[0] == 'test':
                print 'test'
            elif userinput[0] == 'help':
                print 'The current commands are:'
                print '"user" Params: (Username), update a specific id'
                print '"check" No Params: basically go through all ids and check'
                print '"date" Param: (Username), update the lastdate of the user, leave blank for all users'
                print '"quit" to quit'
            elif userinput[0] == 'check':
                logStuff("Running Check Command")
                updateAll()
                updateJSON()
            elif userinput[0] == 'user':
                updateUser(userinput[1])
                updateJSON()
            elif userinput[0] == 'date':
                if len(userinput) <= 1:
                    updateLastdate()
                else:
                    updateLastdate(userinput[1])
                updateJSON()
            elif userinput[0] == 'quit':
                sys.exit(0)
            else:
                print "Command not recongnized " + userinput[0]
    else:
        try:
            opts, args = getopt.getopt(arguments, 'tu:chld:', ['test', 'user=', 'check', 'help', 'list', 'updatedate='])
        except getopt.GetoptError:
            print ('arg not recongnized')
        for opt, arg in opts:
            if opt in ('-t', '--test'):
                print 'test'
            elif opt in ('-u', '--user'):
                updateUser(arg)
                updateJSON()
            elif opt in ('-c', '--check'):
                logStuff("Running Check Command")
                updateAll()
                updateJSON()
            elif opt in ('-h', '--help'):
                print 'The current commands are:'
                print '--user, -u: Params: (Username), update a specific id'
                print '--check, -c: No Params: basically go through all ids and check'
                print '--updatedate, -d: Param: (Username), update the lastdate of the user, leave blank for all users'
            elif opt in ('-l', 'list'):
                print getListIds()
            elif opt in ('-d', '--updatedate'):
                updateLastdate(arg)
            else:
                print 'No argument detected, use -h or --help at the end of console command to bring up a list of arguments'