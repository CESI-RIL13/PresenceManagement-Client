#! /usr/bin/python2.7
import zbar
import time
import wiringpi2 as wpi
import Image
import Synchronisation
import gc
import picamera
import RPi.GPIO as GPIO
from time import sleep

def demo() :
	GPIO.output(7,True)
	sleep(0.1)
	GPIO.output(7,False)
	GPIO.output(13,True)
	sleep(0.1)
	GPIO.output(13,False)
	GPIO.output(11,True)
	sleep(0.1)
	GPIO.output(11,False)
	sleep(0.3)
	GPIO.output(7,True)
	GPIO.output(13,True)
	GPIO.output(11,True)
	sleep(0.5)
	GPIO.output(7,False)
	GPIO.output(13,False)
	GPIO.output(11,False)
	
def buzzerOK() :
	for i in range (20) :
		GPIO.output(12,GPIO.LOW)
		sleep(0.01)
		GPIO.output(12,GPIO.HIGH)
		sleep(0.01)
		
def buzzerKO() :
	for i in range (5) :
		GPIO.output(12,GPIO.LOW)
		sleep(0.02)
		GPIO.output(12,GPIO.HIGH)
		sleep(0.02)

def initialisationGpio() :
	GPIO.setmode(GPIO.BOARD)
	GPIO.setwarnings(False)
	GPIO.setup(7,GPIO.OUT)
	GPIO.setup(11,GPIO.OUT)
	GPIO.setup(13,GPIO.OUT)
	GPIO.setup(12,GPIO.OUT)
	
	demo()
	buzzerOK()

camera = picamera.PiCamera()
camera.resolution = (320,240)
synchro = Synchronisation.Synchronisation()
initialisationGpio()
timeSynchro = 0

while True :
	#os.system("fswebcam -r 320x240 -S 3 --jpeg 50 --quiet --no-banner --save QR.jpg")
	result = ""
	wpi.wiringPiSetup()
	camera.capture('QR.jpg')
	scanner = zbar.ImageScanner()
	scanner.parse_config('enable')
	pil = Image.open('QR.jpg').convert('L')
	#print 'size: ' + str(pil.size)
	width, height = pil.size
	raw = pil.tostring()
	myStream = zbar.Image(width,height,'Y800',raw)
	nb = scanner.scan(myStream)
	timeSynchro += 1
	#print 'nb: ' + str(nb)
	if nb>0 :
		for symbol in myStream :
			if symbol.data != "" or symbol.data != None :
				print symbol.data
				result = synchro.checkUser(symbol.data)
				print 'result: ' + str(result)
	
	if result == 1 :
		#allumer la diode verte
		GPIO.output(7,True)
		buzzerOK()
		sleep(1)
		GPIO.output(7,False)
	if result == 0 :
		#allumer la diode rouge
		GPIO.output(11,True)
		buzzerKO()
		sleep(.1)
		buzzerKO()
		sleep(1)
		GPIO.output(11,False)
	if result == 2 :
		#allumer la diode jaune
		GPIO.output(13,True)
		buzzerKO()
		sleep(1.5)
		GPIO.output(13,False)
		
	if timeSynchro == 50 :
		synchro.routine()
		print 'Synchronisation ready...'
		timeSynchro = 0
		
	gc.collect()
	#time.sleep(0.5)
