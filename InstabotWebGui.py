__author__ = 'Timothy'
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'
@app.route('/testrender', methods = ['POST' , 'GET'])
def testrender():
    if request.method == 'POST':
        if request.form['submit'] == 'Do Something':
            print "Do Something"
        elif request.form['submit'] == 'Do Something Else':
            print "Else"
        else:
            print "placeholder"
    return render_template("test.html")
app.run()
