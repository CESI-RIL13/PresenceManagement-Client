#! /usr/bin/python2.7
# -*-  coding: utf-8 -*-
__author__ = 'ovnislash'
import time
import wiringpi2 as wpi

import RPi.GPIO as GPIO
from time import sleep

class SW(object):
    def __init__(self):
        self.re = 0.0068
        self.fa = 0.0057
        self.do = 0.0038
        self.sib = 0.0042
        self.la = 0.0045
        self.sol = 0.0051
        self.fa2 = 0.0028
        self.duration = 20
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(12,GPIO.OUT)

    def play(self,note,duree):
        for i in range (duree) :
            GPIO.output(12,GPIO.LOW)
            sleep(note)
            GPIO.output(12,GPIO.HIGH)
            sleep(note)

    def main(self):
        self.play(self.re,self.duration)
        sleep(.1)
        self.play(self.re,self.duration)
        sleep(.1)
        self.play(self.re,self.duration)
        sleep(.1)

        self.play(self.fa,self.duration*6)
        sleep(.1)
        self.play(self.do,self.duration*6)
        sleep(.1)

        self.play(self.sib,self.duration)
        sleep(.1)
        self.play(self.la,self.duration)
        sleep(.1)
        self.play(self.sol,self.duration)
        sleep(.1)
        self.play(self.fa2,self.duration*6)
        sleep(.1)
        self.play(self.do,self.duration*3)
        sleep(.1)

        self.play(self.sib,self.duration)
        sleep(.1)
        self.play(self.la,self.duration)
        sleep(.1)
        self.play(self.sol,self.duration)
        sleep(.1)
        self.play(self.fa2,self.duration*6)
        sleep(.1)
        self.play(self.do,self.duration*3)
        sleep(.1)

        self.play(self.sib,self.duration)
        sleep(.1)
        self.play(self.la,self.duration)
        sleep(.1)
        self.play(self.sib,self.duration)
        sleep(.1)
        self.play(self.sol,self.duration*6)

starwars = SW()
starwars.main()
