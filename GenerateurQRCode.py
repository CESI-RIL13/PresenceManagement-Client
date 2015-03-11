#! /usr/bin/python2.7

import pyqrcode

imageTezst = pyqrcode.create('1234567890')
imageTezst.png("superTest.png",scale=8)

