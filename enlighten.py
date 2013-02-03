#!/usr/bin/python
import tlc5940, signal, sys, pygame, logging
from flask import Flask, request
#from sequences import *

app = Flask(__name__)

@app.route("/")
def welcome():
  return "Howdy parner... <a href=https://github.com/eflukx/enlightenPi>EnlightenPi</a> seems to be runnin'<br>For more information please refer to the readme."

@app.route('/fadeto')
def fadeto():
    kleur = pygame.Color(str(request.args.get('color')))
    led = int(request.args.get('led'))
    #print 'Rood: %s, Groen: %s, Blauw: %s' % (kleur.r,kleur.g,kleur.b)
    TLC.fadeto(led * 3, (kleur.r,kleur.g,kleur.b))
    TLC.writeDC()
    return 'Fading LED %s to color %s, %s, %s' % (led, kleur.r, kleur.g, kleur.b)

@app.route("/test")
def test():
  value = int(request.args.get('value'))
  TLC.writeAllDC(value)
  return "Test routine executed."
  
@app.route("/blank")
def blank():
  TLC.writeAllDC(0)
  return "Blanked"

    
@app.route('/setled')
def setled():
  """
  set one or multiple RGB leds at once. If less colours then leds are given, the last
  colour is repeated; if more colours are given, in put is ignored. Input example:
  http://localhost:5000/setm?color=red,GREEN,0x0000ff,0xffffff&led=0,1,3,2
  """
  leds = [int(value) for value in request.args.get('led').split(',')]
  colours = [pygame.Color(str(value)) for value in request.args.get('color').split(',')]
  
  if len(leds) > len(colours):
    for i in range(len(leds)-len(colours)): colours.append(colours[-1])
    logging.info("Number of leds given exceeds colours given.")
    
  coloursRGB = [(value.r, value.g, value.b) for value in colours]

  logging.info(", ".join(["Setting LED %i to %s" % (value[0],value[1]) for value in zip(leds, coloursRGB)]))
  for i in range(len(leds)):
    TLC.setRGB(leds[i] * 3, coloursRGB[i])
  TLC.writeDC(TLC.DCLevels)
  
  return "<br>".join(["Setting LED %i to %s" % (value[0],value[1]) for value in zip(leds, coloursRGB)])

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