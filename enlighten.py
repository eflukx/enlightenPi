#!/usr/bin/python
import tlc5940, signal, sys, pygame, logging
from flask import Flask, request
#from sequences import *

app = Flask(__name__)

@app.route("/")
def welcome():
  return "Howdy parner...<br> enlightenPi seems to be runnin'"

@app.route('/setled')
def setled():
    kleur = pygame.Color(str(request.args.get('color')))
    led = int(request.args.get('led'))
    #print 'Rood: %s, Groen: %s, Blauw: %s' % (kleur.r,kleur.g,kleur.b)
    TLC.setRGB(led * 3, (kleur.r,kleur.g,kleur.b))
    TLC.writeDC()
    return 'Seting LED %s to color %s, %s, %s' % (led, kleur.r, kleur.g, kleur.b)
    
@app.route('/fadeto')
def fadeto():
    kleur = pygame.Color(str(request.args.get('color')))
    led = int(request.args.get('led'))
    #print 'Rood: %s, Groen: %s, Blauw: %s' % (kleur.r,kleur.g,kleur.b)
    TLC.fadeto(led * 3, (kleur.r,kleur.g,kleur.b))
    TLC.writeDC()
    return 'Fading LED %s to color %s, %s, %s' % (led, kleur.r, kleur.g, kleur.b)

def signal_handler(signal, frame):
  print "\nCheerio ol' chap!\n"
  TLC.blinkwriteAllDC(2)
  sys.exit(0)
  
if __name__ == "__main__":
    #logging.basicConfig(filename='myapp.log', level=logging.INFO)
    logging.basicConfig(level=logging.INFO)    
    signal.signal(signal.SIGINT, signal_handler)
    TLC = tlc5940.TLC5940()
    app.run(host='0.0.0.0', debug=True)