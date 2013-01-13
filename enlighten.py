#!/usr/bin/python
import tlc5940, signal, sys, pygame
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
    TLC.setRGBInt(led, (kleur.r,kleur.g,kleur.b))
    TLC.writeDC()
    return 'Seting LED %s to color %s, %s, %s' % (led, kleur.r, kleur.g, kleur.b)

def signal_handler(signal, frame):
  print '\nCheerio old chap.'
  TLC = tlc5940.TLC5940()
  TLC.blinkwriteAllDC(2)
  sys.exit(0)
  
def main():
  TLC.blinkwriteAllDC(3)
  print "MAINEMAINEMAINEMAINEMAINEMAINEMAINEMAINEMAINEMAINEMAINEMAINE"
  while(1):
    sleep(1)
  

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    TLC = tlc5940.TLC5940()
    app.run(host='0.0.0.0', debug=True)
    main()   