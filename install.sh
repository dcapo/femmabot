#!/bin/bash

echo "installing femmabot..."

chmod 755 femmabot.php

mkdir install
cd install

echo "grabbing wget"
brew install wget

echo "grabbing selenium standalone server..."
wget "https://selenium.googlecode.com/files/selenium-server-standalone-2.39.0.jar"
mv selenium-server-standalone-2.39.0.jar ..

echo "grabbing chromedriver..."
wget "http://chromedriver.storage.googleapis.com/2.9/chromedriver_mac32.zip"
echo "unzipping chromedriver..."
unzip chromedriver_mac32.zip
echo "moving chromedriver to /usr/local..."
mv chromedriver /usr/local

echo "grabbing python distribute..."
wget http://python-distribute.org/distribute_setup.py
echo "running python distribute..."
sudo python distribute_setup.py
echo "grabbing python selenium bindings..."
sudo easy_install selenium

echo "============================================================================"
sleep 1
echo "installation comp..."
sleep 0.5
echo "pssssssssssss"
sleep 3
echo "installation comp..."
sleep 0.5
echo "pssssssssss"
sleep 2
echo "installation complete. femmabot initiated."