#!/usr/bin/python
from flask import Flask
from flask import request
import pygame, sys

app = Flask(__name__)

@app.route("/version")
def version():
    return "Howdy partner...<br> We're runnin' kernel version %s on a %s platform..." % (str(sys.version), str(sys.platform))

@app.route("/")
def webroot():
    return "Hi caller, please refer to readme for enlightenPi web API."

@app.route('/seted')
def Setled():
    # show the user profile for that user
    #return 'User %s' % username
    print type(request.args.get('color'))
    if request.args.get('color') == True:
      print "waar!"
    else:
      print " onwaar"
    #return "henk!"
    kleur = pygame.Color(str(request.args.get('color')))
    LED = int(request.args.get('LED'))
    print kleur.hsva[0]
    print 'Rood: %s, Groen: %s, Blauw: %s' % (kleur.r,kleur.g,kleur.b)
    
    return 'Seting LED %s to color %s' % (LED, kleur)
if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
