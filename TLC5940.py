#!/usr/bin/python

#SPI	SPI
#VPRG	GPIO4
#XLAT	GPIO5
#GSCLK	GPIO6

#DPRG L: EEPROM   DC Values (hardwired high)
#DPRG H: Register DC Values (hardwired high)
#VPRG L: 192bit (16*12) PWM values
#VPRG H: 96bit  (16*6)  DC  values
#VPRG V(vprg): prgram epron

import sys, os, signal
import wiringpi, spidev, bitstring
from math import sin, sqrt
from time import sleep

class TLC5940 (object):
  def __init__(self, spibus = 0, spidevice = 0, gsclkpin = 4, blankpin = 3, vprgpin = 5):
    print "Deze versie heeft vprg, blank en gsclock aan GPIO's hangen, de XLAT hangt aan een CE lijn van de SPI"
    print "New pinning, perfboard versie ding"
    self.DCLevels = [0 for x in range(16)]
    
    self.spi = spidev.SpiDev()
    self.spi.open(spibus, spidevice) #/dev/spidev0.0
    self.spi.max_speed_hz = 500000
    print "SPI clock speed:",  self.spi.max_speed_hz, "Hz"
    
    self.gsclkpin = gsclkpin
    self.blankpin = blankpin
    self.vprgpin = vprgpin
    self.gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_PINS)
    self.gpio.pinMode(self.gsclkpin, self.gpio.OUTPUT)
    self.gpio.pinMode(self.blankpin, self.gpio.OUTPUT)
    self.gpio.pinMode(self.vprgpin, self.gpio.OUTPUT)
    
    #Init pins for clockless (DC, no PWM) operation only
    print "Initing display..."
    self.gpio.digitalWrite(self.blankpin, self.gpio.HIGH) #display off, reset the internal counter
    self.gpio.digitalWrite(self.gsclkpin, self.gpio.LOW) 
    self.writeAllPWM(0xfff)
    self.writeAllDC(0)
    self.gpio.digitalWrite(self.blankpin, self.gpio.LOW)  #diplay on, go counter go.
    print "Let's go!"
    self.gpio.digitalWrite(self.gsclkpin, self.gpio.HIGH)  #the zeroth pulse only.. :)
    
  def writeAllPWM(self, value):
    value = int(self.clamp(value, 0, 4095))

    PWMData12 = bitstring.BitArray()
    for x in range(16):
      PWMData12.append('uint:12 = ' + str(value) )
    
    PWMDataPacked = PWMData12.unpack('uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8')
    self.gpio.digitalWrite(self.vprgpin, self.gpio.LOW)
    self.spi.writebytes(PWMDataPacked)
    
  def writeAllDC(self, value):
    value = int(self.clamp(value, 0, 63))

    DCData6 = bitstring.BitArray()
    for x in range(16):
      DCData6.append('uint:6 = ' + str(value) )  
    
    DCDataPacked = DCData6.unpack('uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8')
    self.gpio.digitalWrite(self.vprgpin, self.gpio.HIGH)
    self.spi.writebytes(DCDataPacked)
    
  def writeDC(self):
    DCData = bitstring.BitArray()
    for x in range(15, -1, -1):
      DCData.append('uint:6 = ' + str(int(self.clamp(self.DCLevels[x], 0, 63)) ))  
    DCDataRAW = DCData.unpack('uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8')
    
    self.gpio.digitalWrite(self.vprgpin, self.gpio.HIGH)
    self.spi.writebytes(DCDataRAW)
    
  def setRGBFloat(self, LED, (r,g,b)):
    if LED <= 4: #max 5 rgb LEDs op een TLC5940
      LED *= 3
      self.DCLevels[LED] = self.clamp( int(round(r * 63.5)), 0, 63)
      self.DCLevels[LED + 1] = self.clamp( int(round(g * 63.5)), 0, 63)
      self.DCLevels[LED + 2] = self.clamp( int(round(b * 63.5)), 0, 63)
      return 0
    else:
      raise Exception("Whoopsie.. Ik kan niet meer dan 5 RGB LEDs aansturen.")
      return -1 #tjah.. hier komtie dus nooit..
      
  def setRGBInt(self, LED, (r,g,b)):
    if LED <= 4: #max 5 rgb LEDs op een TLC5940
      LED *= 3
      self.DCLevels[LED] = self.clamp(r >> 2, 0, 63)
      self.DCLevels[LED + 1] = self.clamp(g >> 2, 0, 63)
      self.DCLevels[LED + 2] = self.clamp(b >> 2, 0, 63)
      return 0
    else:
      raise Exception("Whoopsie.. Ik kan niet meer dan 5 RGB LEDs aansturen.")
      return -1 #tjah.. hier komtie dus nooit.. 
  
  def blinkwriteAllDC(self, times):
    for y in range(times):
      self.writeAllDC(30) #16, prettig aan de ogen..
      sleep(0.02)
      self.writeAllDC(0)
      sleep(0.05)
      
  def clamp(self, input, minOut, maxOut):
    return max(minOut, min(input, maxOut))
    
def signal_handler(signal, frame):
  print '\nComputer says: bye bye motherfucker'
  TLC = TLC5940()
  TLC.blinkwriteAllDC(2)
  sys.exit(0)
  
def sCurve(x):
  return x / sqrt(1 + x ** 2)
  
def main():
  signal.signal(signal.SIGINT, signal_handler)
  TLC = TLC5940()
  TLC.blinkwriteAllDC(3)
  
  trein1 = [4,8,16,63,16,8,4,0,0,0,0,0,0,0,0,0]
  trein2 = [1,1,1, 2,2,2, 4,4,4, 8,8,8, 16,16,16, 32,32,32, 63,63,63, 32,32,32, 16,16,16, 8,8,8, 4,4,4, 2,2,2, 1,1,1, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
  trein3 = [0.015, 0.031, 0.0625, 0.125, 0.25, 0.5, 1.0, 0.5, 0.25, 0.125, 0.0625, 0.031, 0.015, 0, 0, 0, 0, 0, 0, 0, 0, 0]
  AABColor = [1, 135, 119]
  INGColor =  [255, 85, 2]
  RaboColor = [7, 3, 246]     #feller dan normaal.
  SNSColor = [119, 112, 255]  #[135, 142, 255]
  #SiebColor =  [154,203,60]   #[148,233,0]
  WNColor = [204, 0, 0]
  SiebColor = [63,63,63,63,63,63,63,63,63, 63,63,63, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

  banks = AABColor + INGColor + RaboColor + SNSColor
  
  offset = 0
  
  while(1):
    offset += 3

    for i in range(15):  
      fadein = TLC.clamp((offset/3)/60.0,0,1)
      	  
      TLC.DCLevels[i] = trein2[(i - offset) % len(trein2)]
      
      TLC.DCLevels[i] = int(AABColor[(i - offset) % len(AABColor)] * fadein) >> 2
      TLC.DCLevels[i] = int(INGColor[(i - offset) % len(INGColor)] * fadein) >> 2
      #TLC.DCLevels[i] = int(SNSColor[(i - offset) % len(SNSColor)] * fadein) >> 2
      #TLC.DCLevels[i] = int(WNColor[(i - offset) % len(WNColor)] * fadein) >> 2
      #TLC.DCLevels[i] = int(RaboColor[(i - offset) % len(RaboColor)] * fadein) >> 2
      #TLC.DCLevels[i] = int(SiebColor[(i - offset) % len(SiebColor)] * fadein) >> 2
	  
      #TLC.DCLevels[i] = int(banks[(i - offset) % len(banks)] * 1) >> 2
      #TLC.DCLevels[i] = int(63 * sCurve(fadein))
      #TLC.DCLevels[i] = int(1 * (offset & 1))
      #print sCurve(fadein), fadein
      
      #TLC.setRGBInt(0,INGColor[0:3])
    sleep(0.05)
    TLC.writeDC()
  sys.exit(0)

if __name__ == "__main__":
  main()
