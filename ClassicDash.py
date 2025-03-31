import os
import pygame 
import pickle
import RPi.GPIO as GPIO # I have rpi-lgpio
import spidev
import serial
import time

#variables lots of them
angletan=0
battery = 5
current_odom = 0
disttrvled = float(0)
fuel = 0
GPGGA_buffer = 0
gpgga_info = "$GPGGA,"
gpvtg_info = "$GPVTG,"
moving_speed = 0
run_time = time.time () # out of order for a reason
past_time = run_time
press_start_time = None
speed = 0
temp = 0

# Initialize tripA, tripB, odom, and oil pickle will update
tripA = 0
tripB = 0
odom = 0
oil = 0

# class variables
INDICATOR = ['odom', 'tripA', 'tripB', 'oil']
#DASHES = ['classic', 'analog', 'digital'] # open a file classic.py, analog.py, digital.py

 #Constants or pin identification
DEBOUNCE_DELAY = 0.2
HALL_SENSOR_PIN = 23
HBPIN = 6
FAN_PIN = 27  # Replace with the actual GPIO pin number connected to the fan
SET_PIN = 22
SELECT_PIN = 25
TEMP_THRESHOLD = 45.0  # Temperature in Celsius to activate the fan
TURNPIN = 5

# Array to store the last 4 readings
speed_readings = [0, 0, 0, 0]

# Define SPI parameters for MAX6675
spi = spidev.SpiDev()
ser = serial.Serial ("/dev/ttyS0")
# GPIO setup
GPIO.setmode(GPIO.BCM)
    # GPIO input setup
GPIO.setup(HALL_SENSOR_PIN, GPIO.IN)
GPIO.setup(HBPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SELECT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(TURNPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # GPIO output setup
GPIO.setup(FAN_PIN, GPIO.OUT)

pygame.init()
screen = pygame.display.set_mode((1080, 1080),pygame.FULLSCREEN)
pygame.display.set_caption("JAZZ DASH")

    # Load images (replace with your image paths)
background = pygame.image.load("digital5.png").convert_alpha()
compass_ring = pygame.image.load("compring.png").convert_alpha()

    # Get image rectangles
rect1 = background.get_rect()
rect1.topleft = (0, 0)
#rect2.center = (540, 190)

    # odometer trip initialize
with open("odometer.txt", "rb") as file:
    data = pickle.load(file)
    tripA = data.get('tripA')
    tripB = data.get('tripB')
    odom = data.get('odom')
    oil = data.get('oil')
    
text_font_small = pygame.font.SysFont("URWGothic-Book", 42)
text_font = pygame.font.SysFont("URWGothic-Book", 72)
text_font_large = pygame.font.SysFont("URWGothic-Book", 285)


# functions



def update_odometer(): # update trip, odometer, oil
    global tripA, tripB, odom, oil  # Ensure these variables are accessible
    disttrvled = speed * .000278 # not sure on number
    if disttrvled > 0:
        tripA = tripA + disttrvled #DashboardData.tripA ?
        tripB = tripB + disttrvled
        odom = odom + disttrvled
        oil = oil + disttrvled                   
        with open("odometer.txt", "wb") as file:
            pickle.dump({'tripA': tripA, 'tripB': tripB, 'odom': odom, 'oil': oil}, file)
    return tripA, tripB, odom, oil #new readings

def set_button_callback(channel):
    global current_odom, press_start_time, tripA, tripB, odom, oil

    # Check if the button is pressed
    if GPIO.input(SET_PIN) == GPIO.LOW:
        if press_start_time is None:
            press_start_time = time.time()
            sb = pygame.image.load("setbutton.png").convert_alpha()
            screen.blit(sb, (10, 540))
    
    else:
        if press_start_time is not None:
            press_duration = time.time() - press_start_time
            press_start_time = None

            if press_duration >= 2:  # Hold for 2 seconds to reset add pickle
                #0 is odom, 1 is tripA, 2 is tripB, 3 is oil
                with open("odometer.txt", "wb") as file:
                    data = {'tripA': tripA, 'tripB': tripB, 'odom': odom, 'oil': oil}
                    if current_odom == 0:
                        print("dont reset the odom")
                    elif current_odom == 1:
                        data['tripA'] = 0
                        print(f"Resetting {INDICATOR[current_odom]}")
                        tripA = 0 
                    elif current_odom == 2:
                        data['tripB'] = 0
                        print(f"Resetting {INDICATOR[current_odom]}")
                        tripB = 0  
                    elif current_odom == 3:
                        data['oil'] = 0
                        print(f"Resetting {INDICATOR[current_odom]}")
                        oil = 0   
                    pickle.dump(data, file)
                current_odom = 0
            else:  # Short press to select next item
                current_odom = (current_odom + 1) % len(INDICATOR)
                print(f"Selected {INDICATOR[current_odom]}")

def read_channel(channel):
        # Open SPI bus 0, device (chip select) 0
    spi.open(0, 0)
        # Set SPI speed and mode
    spi.max_speed_hz = 1350000
    spi.mode = 0
        # Ensure the channel is valid (0-7)
    
        # Perform SPI transaction and store returned bits in 'r'
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
        # Process returned bits and calculate the value
    data = ((adc[1] & 3) << 8) + adc[2]
        # close spi for othere process
    spi.close()
    return data

# Function to convert data to voltage level
def convert_for_voltage(data, VREF=16.4):
    voltage = (data * VREF) / float(1023)
    return voltage

def convert_for_fuel(data, VREF=147):
    voltage = ((data - .05)* VREF) / float(1023)
    return voltage



def read_temp(temp):
    spi.open(1, 0)
    spi.max_speed_hz = 1000000
    spi.mode = 0b10  # SPI mode 0b10 (CPOL=1, CPHA=0)

    # Read two bytes of data
    data = spi.readbytes(2)
    
    # Combine bytes and shift to get temperature data (ignoring the fault bit)
    temp_data = (data[0] << 8 | data[1]) >> 3
    
    # Convert to Celsius (0.25 degrees per bit)
    celsius = temp_data * 0.34
    
    temp = celsius * 9.0 / 5.0 + 32.0
    
    spi.close()
    
    return temp

def measure_speed(speed):
    """Measures the frequency of the Hall effect sensor."""
    last_state = GPIO.input(HALL_SENSOR_PIN)
    last_time = time.time()
    measurements_taken = 0

    while measurements_taken < 4:  # Change this to the number of measurements you want to take
        current_state = GPIO.input(HALL_SENSOR_PIN)
        current_time = time.time()
        if current_state == last_state and current_time - last_time > 1:  # may have to increase this time
            print("Frequency is equal to zero.")
            print(f"Speed: {speed:.1f}MPH")
            frequency = 0
            speed = 0
            measurements_taken += 1
        
        if current_state != last_state:
            if current_state == 1:  # Rising edge
                time_difference = current_time - last_time
                if time_difference > 0:
                    frequency = 1 / time_difference
                    print(f"Frequency: {frequency:.2f} Hz")
                    cal_speed = (frequency * 10) / 10.476
                    speed_readings[measurements_taken % 4] = cal_speed
                    if measurements_taken >= 3:
                        total_speed = sum(speed_readings[-3:]) / 3
                        print(f"Total Speed of last 3 readings: {total_speed:.1f}MPH")
                        speed = total_speed
                    measurements_taken += 1
                else:
                    print("Frequency: Infinite or Undefined (Time difference is zero)")
                last_time = current_time
            last_state = current_state
    return speed

def pi_fan():
    """Gets the CPU temperature using the vcgencmd command."""
    res = os.popen("vcgencmd measure_temp").readline()
    temp = float(res.replace("temp=", "").replace("'C\n", ""))
    if temp > TEMP_THRESHOLD:
        GPIO.output(FAN_PIN, GPIO.HIGH)  # Turn fan on
        print("Fan ON")
    else:
        GPIO.output(FAN_PIN, GPIO.LOW)  # Turn fan off
        print("Fan OFF")

def draw_text(text, font, text_col, x, y):
  img = font.render(text, True, text_col)
  screen.blit(img, (x, y))


def blitRotate(surf, image, pos, originPos, angle):

    # offset from pivot to center
    image_rect = image.get_rect(topleft = (pos[0] - originPos[0], pos[1]-originPos[1]))
    offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center
    
    # roatated offset from pivot to center
    rotated_offset = offset_center_to_pivot.rotate(-angle)

    # roatetd image center
    rotated_image_center = (pos[0] - rotated_offset.x, pos[1] - rotated_offset.y)

    # get a rotated image
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)

    # rotate and blit the image
    surf.blit(rotated_image, rotated_image_rect)

# Setup event detection on the button pin
GPIO.add_event_detect(SET_PIN, GPIO.BOTH, callback=set_button_callback, bouncetime=int(DEBOUNCE_DELAY * 1000))  

# Initialize the timer
last_update_time = time.time()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
                running = False
                
    background = pygame.image.load("tan5.png").convert_alpha()
    spdneedle = pygame.image.load("spdneedle.png").convert_alpha()
    rect1 = background.get_rect()
    rect1.topleft = (0, 0)
            # Clear the screen
    screen.fill((255, 255, 255))  # White background
    screen.blit(background, rect1)
            #call functions
    temp = read_temp(temp)
    pi_fan()
    print(f"Temperature: {temp:.2f} F ")
    fuel_data = read_channel(0)
    battery_data = read_channel(1)
    fuel = convert_for_fuel(fuel_data)
    battery = convert_for_voltage(battery_data)
    speed = measure_speed(speed)
            # Update odometer every second
    current_time = time.time()
    if current_time - last_update_time >= 1 and speed > 0:
        tripA, tripB, odom, oil = update_odometer()
        last_update_time = current_time
        print("updating distance travelled")
    if current_time - last_update_time >= 1: # update odometer counter every second
        last_update_time = current_time # reset the timer
        print("no reason to update")
    
            # Print out results
    print(f"Fuel: Data = {fuel_data}, Percent= {fuel:.2f}")
    print(f"Battery: Data = {battery_data}, Voltage = {battery:.2f}V")
    
    hb_state = GPIO.input(HBPIN)
    turn_state = GPIO.input(TURNPIN)
    #print(f"HBPIN state: {hb_state}")
    #time.sleep(.1)
    #print(f"TURNPIN state: {turn_state}")
    #time.sleep(.1)

    if hb_state == GPIO.HIGH:
        hb = pygame.image.load("tanhb.png").convert_alpha()
        screen.blit(hb, (173, 815)) #location
    if turn_state == GPIO.HIGH:
        tn = pygame.image.load("tanturn.png").convert_alpha()
        screen.blit(tn, (804, 815)) #location
        
    #select trip, oil or odometer or display
    if current_odom == 0:
        draw_text(f"Odom {odom: .1f}", text_font, (10, 85, 163), 375, 770) #trip, oil, odometer maybe button_select
    elif current_odom == 1:
        draw_text(f"Trip A {tripA: .1f}", text_font, (10, 85, 163), 375, 770) #trip, oil, odometer maybe button_select
    elif current_odom == 2:
        draw_text(f"Trip B {tripB: .1f}", text_font, (10, 85, 163), 375, 770) #trip, oil, odometer maybe button_select
    elif current_odom == 3:
        draw_text(f"Oil {oil: .1f}", text_font, (10, 85, 163), 375, 770) #trip, oil, odometer maybe button_select   
    
    draw_text(f"Volts:   {battery:.1f} ", text_font, (10, 85, 163), 375, 882) # voltage
    draw_text(f"Fuel:    {fuel:.2f} ", text_font, (10, 85, 163), 375, 826) # fuel
    draw_text(f"Temp:  {temp:.1f} F ", text_font, (10, 85, 163), 375, 938) #fahrenheit
    
    angletan =  111.5 - (speed * 2.24) #angletan 0 MPH at 111.5 
        
    #images for all below
    blitRotate(screen, spdneedle, (541, 543), (360, 935), angletan)
    
    # if scooter is off shutdown pi hopefully a good battery reading first
    if battery < 5: 
        os.system("sudo shutdown -h now")
    
        # Update the display
    pygame.display.flip()
    time.sleep(.01) 

pygame.quit()



