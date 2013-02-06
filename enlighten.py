#!/usr/bin/python
import tlc5940, signal, sys, pygame, logging
from flask import Flask, request
#from sequences import *

app = Flask(__name__)

@app.route("/")
def welcome():
  return "Howdy partner... <a href=https://github.com/eflukx/enlightenPi>EnlightenPi</a> seems to be runnin'<br>For more information please refer to the readme."

@app.route('/fadeto')
def fadeto():
  if request.args.get('duration') == None:
    duration = 0.5
  else:
    duration = float(request.args.get('duration'))

  if request.args.get('color') == None:
    return "argument 'color' needs to be present"
  else:
    colours = [pygame.Color(str(value)) for value in request.args.get('color').split(',')]
  
  if request.args.get('led') == None:
    leds = range(TLC.numberof_RGBleds)
  else:
    leds = [int(value) for value in request.args.get('led').split(',')]
  
  if len(leds) > len(colours):
    for i in range(len(leds)-len(colours)): colours.append(colours[-1])
    logging.info("Number of leds given exceeds colours given. Extending with last colour")
  
  newRGBlevels = []
  for value in colours:
    newRGBlevels += [value.r, value.g, value.b]  #new RGB levels list of tuples.
  
  RGBlevels = [TLC.DCLevels[x] << 2 for x in range(len(TLC.DCLevels))]             #Get existing old levels (new values will overwrite)
  
  logging.info(", ".join(["Fading LED %i to %s" % (zpper[0], zpper[1]) for zpper in zip(leds,colours)]))
  for i in range(len(leds)):
    offset = leds[i] * 3 #current led offset
    RGBlevels[offset:offset + 3] = newRGBlevels[i*3:i*3 + 3]
    
  print RGBlevels
  print len(RGBlevels)
    
  TLC.fadeto(RGBlevels, duration = duration)
  return "<br>".join(["Faded LED %i to %s in %s seconds" % (zpper[0], zpper[1], duration) for zpper in zip(leds,colours)])

@app.route('/fadeall')
def fadeall():
  kleur = pygame.Color(str(request.args.get('color')))
  color = [[kleur.r,kleur.g,kleur.b][c % 3] for c in range(16)]
  TLC.fadeto(color)
  return 'Fading all LEDs to color %s, %s, %s' % (kleur.r, kleur.g, kleur.b)

@app.route("/test")
def test():
  #value = int(request.args.get('value'))
  #TLC.writeAllDC(value)
  print request.args.get('value')
  if request.args.get('value') == None:
    print "noeeoen"
    return "value in None"
  return "Test routine executed. Value is %s" % request.args.get('value')
  
@app.route("/blank")
def blank():
  TLC.writeAllDC(0)
  return "Blanked"
  
@app.route("/unblank")
def unblank():
  TLC.writeDC(TLC.DCLevels)
  return "Blanking disabled"
  
@app.route('/setled')
def setled():
  """set one or multiple RGB leds at once. If less colours then leds are given, the last
  colour is repeated; if more colours are given, in put is ignored. Input example:
  http://localhost:5000/setm?color=red,GREEN,0x0000ff,0xffffff&led=0,1,3,2
  """
  if request.args.get('color') == None:
    return "argument 'color' needs to be present"
  else:
    colours = [pygame.Color(str(value)) for value in request.args.get('color').split(',')]
  
  if request.args.get('led') == None:
    leds = range(TLC.numberof_RGBleds)
  else:
    leds = [int(value) for value in request.args.get('led').split(',')]

  if len(leds) > len(colours):
    for i in range(len(leds)-len(colours)): colours.append(colours[-1])
    logging.info("Number of leds given exceeds colours given. Extending with last colour")
    
  coloursRGB = [(value.r, value.g, value.b) for value in colours]

  logging.info(", ".join(["Setting LED %i to %s" % (value[0],value[1]) for value in zip(leds, coloursRGB)]))
  for i in range(len(leds)):
    TLC.setRGB(coloursRGB[i], leds[i] * 3)
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
    app.run(host='0.0.0.0', debug=False)