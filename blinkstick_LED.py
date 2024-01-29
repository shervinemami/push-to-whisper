# coding: utf-8

# Provides a way to change the LED color of a BlinkStick USB device
# By Shervin Emami (shervin.emami@gmail.com), Jan 2024


LED_BRIGHTNESS = 5      # LED Brightness can be upto 255. I like faint values around 5


try:
    from blinkstick import blinkstick
    bstick = blinkstick.find_first()
except:
    bstick = None

if bstick:
    print("Found BlinkStick USB LED", bstick.get_serial())
else:
    print("Couldn't access the BlinkStick USB LED")


# Show the current mode, using the USB LED.
# Examples for grammarMode can be "Normal", "Command", "off", "disabled", "sleeping"
def updateLED(grammarMode = "Normal"):
    global bstick
    try:
        if bstick:
            #print("In updateLED ", grammarMode)
            V = LED_BRIGHTNESS  # LED Brightness upto 255
            # Set my BlinkStick LED to green (ON, Normal mode) or blue (ON, Command mode)
            if grammarMode == "Normal":
                bstick.set_color(red=0, green=V, blue=0)
            elif grammarMode == "Yellow":
                bstick.set_color(red=V, green=V, blue=0)
            elif grammarMode == "Orange":
                bstick.set_color(red=V, green=V/3, blue=0)
            elif grammarMode == "Pink":
                bstick.set_color(red=V*1.2, green=V/3, blue=V/2.5)
            elif grammarMode == "BlueGreen":
                bstick.set_color(red=1, green=9, blue=3)
            elif grammarMode == "disabled":
                # Set my BlinkStick LED to red (disabled)
                bstick.set_color(red=V*2, green=0, blue=0)
            elif grammarMode == "sleeping":
                # Set my BlinkStick LED to purple (sleeping)
                bstick.set_color(red=1, green=0, blue=0)
            elif grammarMode == "off":
                # Set my BlinkStick LED to black (off)
                bstick.set_color(red=0, green=0, blue=0)
            else:
                bstick.set_color(red=0, green=0, blue=V*1.2)
    except:
        print("Warning: Couldn't access the BlinkStick USB LED")
        pass
