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

import wiringpi, spidev, bitstring, logging
from time import sleep
logger = logging.getLogger(__name__)

class TLC5940 (object):
  def __init__(self, numberof_TLC5940 = 1, spibus = 0, spidevice = 0, gsclkpin = 4, blankpin = 3, vprgpin = 5):
    """
    Class to control a TLC5940 LED controller. This was made for use on a Raspberry PI, in conjunction with
    the WiringPi-Python library. Probably isn't hard to get to work on other platforms as well.
    This version has vprg, blank en gsclock connected to GPIO's, XLAT is connected
    to the CE SPI pin. Multiple TLC5940's can be daisy chained. (soon)
    """
    
    self.numberof_TLC5940 = numberof_TLC5940
    self.numberof_leds = self.numberof_TLC5940 * 16
    self.numberof_RGBleds = int(self.numberof_leds // 3)
    
    self.DCLevels = [0 for x in range(self.numberof_leds)]  #internal DC register
    
    logger.info("Configured %i TLC5940 with %i channels. (max %i RGB channels)" % (self.numberof_TLC5940, self.numberof_leds, self.numberof_RGBleds))
    self.spi = spidev.SpiDev()
    self.spi.open(spibus, spidevice) #/dev/spidev0.0
    self.spi.max_speed_hz = 500000
    logger.info("Setting SPI clock speed to %i Hz." % self.spi.max_speed_hz)
    
    self.gsclkpin = gsclkpin
    self.blankpin = blankpin
    self.vprgpin = vprgpin
    self.gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_PINS)
    self.gpio.pinMode(self.gsclkpin, self.gpio.OUTPUT)
    self.gpio.pinMode(self.blankpin, self.gpio.OUTPUT)
    self.gpio.pinMode(self.vprgpin, self.gpio.OUTPUT)
    
    #Init pins for clockless (DC, no PWM) operation only
    logger.info("Initializing TLC5940...")
    self.gpio.digitalWrite(self.blankpin, self.gpio.HIGH) #display off, reset the internal counter
    self.gpio.digitalWrite(self.gsclkpin, self.gpio.LOW) 
    self.writeAllPWM(0xfff)
    self.writeAllDC(0)
    self.gpio.digitalWrite(self.blankpin, self.gpio.LOW)  #diplay on, go counter go.
    self.gpio.digitalWrite(self.gsclkpin, self.gpio.HIGH)  #the zeroth pulse only.. :)
    logger.info("...Let's go!")
    
  def writeAllPWM(self, value = 0):
    """
    Writes all PWM values to a specific value, only writes directly to chip, not in a internal register.
    No scaling is applied, values from 0 to 4095
    """
    value = int(self.clamp(value, 0, 4095))

    PWMData12 = bitstring.BitArray()
    for x in range(16):
      PWMData12.append('uint:12 = ' + str(value) )
    
    PWMDataPacked = PWMData12.unpack('uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8, uint:8')
    self.gpio.digitalWrite(self.vprgpin, self.gpio.LOW)
    self.spi.writebytes(PWMDataPacked)
    
  def writeAllDC(self, value = 0):
    """
    Writes all DC values to a specific value, only writes directly to chip, not in internal register.
    No scaling is applied, values from 0 to 63
    """
    value = int(self.clamp(value, 0, 63))
    self.writeDC([value for i in range(self.numberof_leds)])
      
  def writeDC(self, input = []):  
    """
    Writes a given DC register to the TLC5940 IC.
    Not multi-chip capable yet!!
    """
    if len(input) == 0:
      register = list(self.DCLevels)
    else:
      register = list(input)

    register.reverse()      #Reversal is somehow needed..
    DCdata_packed = []
    for i in range(0,len(register),4): DCdata_packed += self.pack_4to3(register[i:i+4])

    self.gpio.digitalWrite(self.vprgpin, self.gpio.HIGH)
    self.spi.writebytes(DCdata_packed)

  def fadeto(self, targetlevels = [], offset = 0, steps = 64, duration = 0.2):
    """
    Fades linearly to new value, writes to internal register and IC directly.
    Usable for any number of LEDs, no specific colour handling.
    Foe now no delay nor timing is implemented.
    """
    count = len(targetlevels)
    if (offset + count) > self.numberof_leds:
      logger.warning("Whoopsie.. Cannot address over %i LEDs. Truncating input." % self.numberof_leds)
      count = self.numberof_leds - offset
    
    targetlevels = [self.clamp(x >> 2, 0, 63) for x in targetlevels]              #scale and boundary confinement
    _origlevels = self.DCLevels[offset:(offset + count)]                            #Save original levels
    _deltas = [targetlevels[i] - self.DCLevels[offset + i] for i in range(count)]   #Calculate deltas
    
    for i in range(steps + 1):                                                      #Do fade loop
      scaler = float(i)/steps
      self.DCLevels[offset:(offset + count)] = [int(_origlevels[i] + (_deltas[i] * scaler)) for i in range(count)]
      self.writeDC(self.DCLevels)
      sleep(duration/steps)

  def setRGB(self, value = [], offset = 0):
    """
    Sets (doesn't write out to IC) the given value in the local DC register. Values in 0-255.
    """
    if (offset + 3) <= self.numberof_leds:
      self.DCLevels[offset:offset + 3] = [self.clamp(value[i] >> 2, 0, 63) for i in range(3)]
      return True
    else:
      logger.warning("Whoopsie.. Cannot address over %i RGB LEDs." % self.numberof_RGBleds)
      return False
  
  def getRGB(self, offset = 0):
    """
    Returns one RGB value (scaled to RGB888) as a list from internal DC register, starting from offset.
    """
    if (offset + 3) <= self.numberof_leds:
      return [value << 2 for value in self.DCLevels[offset:offset + 3]]
    else:
      return []
  
  def blinkwriteAllDC(self, times):
    for y in range(times):
      self.writeAllDC(16) #16, easy on the eyes...
      sleep(0.02)
      self.writeAllDC(0)
      sleep(0.05)
      
  def clamp(self, input, minOut, maxOut):
    return max(minOut, min(input, maxOut))
    
  def pack_4to3(self, inp):
    """
    converts 4 6bit integers to 3 8bit integers
    output bytes: 00000011 11112222 22333333
    """
    if len(inp) != 4:
      logger.error("Input to pack_4to3 should have 4 elements.")
      return []
    inp = [value & 63 for value in inp] 
    return [(inp[0] << 2) & 255 | inp[1] >> 4, (inp[1] << 4) & 255 | inp[2] >> 2, (inp[2] << 6) & 255 | inp[3]]

  def pack_2to3(self, inp):
    """
    converts 2 12bit integers to 3 8bit integers
    output bytes: 00000000 00001111 11111111
    """
    if len(inp) != 2:
      logger.error("Input to pack_2to3 should have 2 elements.")
      return []
    inp = [value & 4095 for value in inp] 
    return [inp[0] >> 4, (inp[0] << 4) & 255 | inp[1] >> 8, inp[1] & 255]