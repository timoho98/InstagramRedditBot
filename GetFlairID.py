import praw
REDDIT_USERAGENT = 'useragent'
REDDIT_USERNAME = 'username'
REDDIT_PASSWORD = 'password'
submissionurl = 'submissionurl' #for flair choices
r = praw.Reddit(user_agent=REDDIT_USERAGENT)
r.login(REDDIT_USERNAME, REDDIT_PASSWORD)
submission = praw.objects.Submission.from_url(r,url= submissionurl)

submissionflairjson = submission.get_flair_choices()
for f in submissionflairjson['choices']:
    print f['flair_text']
    print f['flair_css_class']
    print f['flair_template_id']
    print str(f['flair_text_editable'])
    print "\n"
