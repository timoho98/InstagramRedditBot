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
INSTAGRAM_CLIENT_ID = config.get("instagram", "clientid")
INSTAGRAM_CLIENT_SECRET = config.get("instagram", "clientsecret")
IMGUR_CLIENT_ID = config.get("imgur", "clientid")
IMGUR_CLIENT_SECRET = config.get("imgur", "clientsecret")
REDDIT_USERAGENT = config.get("reddit", "userAgent")
REDDIT_USERNAME = config.get("reddit", "username")
REDDIT_PASSWORD = config.get("reddit", "password")
REDDIT_SUBREDDIT = config.get("reddit", "subreddit")
TARGET_JSON_FILE = config.get("File", "Name")
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

# automaticly adds the new like '\n' at the end of every entry
def logStuff(text):
    time_ = datetime.datetime.utcfromtimestamp(time.time()).strftime('%H:%M:%S')
    date = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d')
    print ("Logged: '" + text + "' in " + date + ".log at " + time_)
    log = open(os.path.join(current_path + '\\logs', date + ".log"), "ab")
    log.write(date + " " + time_ + ": " + text + '\n')
    log.close()


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


# check if username exists in data jsoniddata
def checkIfNameInData(username):
    for i in jsonIdData:
        if i['name'] == username:
            return True
    return False


# check if id exists in data jsoniddata
def checkIdInData(userId):
    for i in jsonIdData:
        if i['id'] == userId:
            return True
    return False


# choose flair based on username returns a html flair id, params needed, username
def chooseFlair(username):
    for i in jsonIdData:
        if i['name'] == username:
            flairid = i['flairid']
            return flairid


# more updated version of write to date updates json file with data and username
def writeToDateJson(date, username):
    if type(date) is int:
        global updatedJson  # updates global var
        for j in updatedJson:
            # Make sure you actually write the 'LastDate' as media not in chronological order
            # TODO attempt to make it chornological
            if j['name'] == username:
                if j['lastdate'] < date:
                    j['lastdate'] = date
                    logStuff('Updated last date to ' + str(date) + ' for:' + username)
    else:
        print 'Date provided to writeToDateJson not a int'


# Gets the last part of a instagramlink for later uses
def getEndOfLink(link):
    endpart = link.split('/')
    return endpart[4]


# List Ids that exist in the json file
def getListIds():
    idString = ''
    for id in jsonIdData:
        idString += id['name']
        idString += '\n'
    return idString


# Get id from name input
def getIdFromName(name):
    for i in jsonIdData:
        if i['name'] == name:
            return i['userid']


# Get Json Dict from id or name
def getJsonDict(id):
    if type(id) is int:
        for i in jsonIdData:
            if i['id'] == id:
                return i
    if type(id) is str:
        for i in jsonIdData:
            if i['name'] == id:
                return i


# List ids as well as last dates
def getListIdDate():
    idDateString = []
    for id_ in jsonIdData:
        idDateString.append(id_['name'] + ' - ' + str(datetime.datetime.utcfromtimestamp(id_['lastdate'])) + '\n')
    return idDateString


# Get json of most recent media param Userid dict from json
def getMediaJSON(userId):
    mediaReturn = requests.get('https://api.instagram.com/v1/users/' + str(
        userId['userid']) + '/media/recent/?client_id=' + INSTAGRAM_CLIENT_ID)
    logStuff("Request JSON of InstaId:" + str(userId['name']) + " User Id:" + str(userId['userid']))
    mediaReturnJSON = mediaReturn.json()
    return mediaReturnJSON


# Generates Text for comment
def generateCommentText(source):
    commentString = "[Source](" + source + ")"  # format source text
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


# Post to subreddit, param url, and add comment at the end of submission
def submitToReddit(url, linkCaption, source):
    redditSubmission = postsubreddit.submit(title=linkCaption, url=url)
    # TODO add more things to comment
    logStuff("Submitted Link to Reddit at " + redditSubmission.short_link)
    redditSubmission.add_comment(generateCommentText(source))
    return redditSubmission


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
        submittedLink = submitToReddit(url=imgurjson['data']['link'], linkCaption=caption, source=imageJson['link'])
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
    submittedLink = submitToReddit(url=videoUrl, linkCaption=caption, source=videoJson['link'])
    r.select_flair(item=submittedLink, flair_template_id=chooseFlair(username=instagramUsername))
    logStuff("Selected flair for " + instagramUsername)
    logStuff("Finished Processing video for " + instagramUsername + " Videoid:" + videoJson['id'])


# Check instagram for new pictures with particular id
def updateWithId(iddict):
    mediaJSON = getMediaJSON(iddict)
    # TODO Change to logstuff
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


if __name__ == "__main__":  # Only runs if not loaded as a module
    arguments = sys.argv[1:]  # Get arguments after the command run
    try:
        opts, args = getopt.getopt(arguments, 'tu:chl', ['test', 'user=', 'check', 'help', 'list'])
    except getopt.GetoptError:
        print ('arg not recongnized')
    for opt, arg in opts:
        if opt in ('-t, --test'):
            print 'test'
        elif opt in ('-u', '--user'):
            if checkIfNameInData(username=arg):
                for id in jsonIdData:  # Parse through list to find the id there is probably a better way to do this or organize data better but idk what it is
                    if id['name'] == str(arg):
                        updateWithId(id)
                with open(os.path.join(current_path, TARGET_JSON_FILE),'wb') as newjsonfile:  # Part where we write to file
                    json.dump(updatedJson, newjsonfile, indent=4, separators=(', ', ': '))
                logStuff("Updated Jsonfile")
            else:
                print "error " + arg + " does not exist in config"
        elif opt in ('-c', '--check'):
            logStuff("Running Check Command")
            for ids in jsonIdData:
                updateWithId(ids)
            with open(os.path.join(current_path, TARGET_JSON_FILE), 'wb') as newjsonfile:  # Part where we write to file
                json.dump(updatedJson, newjsonfile, indent=4, separators=(', ', ': '))
            logStuff("Updated Jsonfile")
        elif opt in ('-h', '--help'):
            print 'The current commands are:'
            print '--user, -u: Params: (Username), update a specific id'
            print '--check, -c: No Params: basically go through all ids and check'
        elif opt in ('-l', 'list'):
            print getListIds()
        else:
            print 'No argument detected, use -h or --help at the end of console command to bring up a list of arguments'