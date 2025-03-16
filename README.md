# ScooterDash
# 5 inch dash with GPS for a scooter
This is my first github project. my hope is someone struggling to get there project to work may find my code useful.

This code is free to use at your own discretion. I have struggled with MAX31855 and MAX6675 to work with raspberry pi zero 2w
Make sure you turn on SPI in config. I moved my MAX6675 to SPI1 because I had MCP3008 already using SPI0. In order to use 
SPI1 you need to update your config file. You can do this by opening the micro sd in a computer and add this line to your code...
be sure to check out pinout.xyz/pinout, there is some very useful information there about zero's pinouts

"dtoverlay=spi1-3cs"

# my config file looks like this with spi on...

dtparam=spi=on #spi on

# enable spi 1

dtoverlay=spi1-3cs # enable SPI1 this will give you SPI1 with CE0,CE1,CE2 

# google ai made part of my code I had to make some changes to get the right spi mode. Google thinks it is mode 1 which will draw a fault
I use 0b10 or mode 2. CS low to read, falling edge of the clock.
