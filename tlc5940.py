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

import wiringpi, spidev, bitstring
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