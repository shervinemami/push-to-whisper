# coding: utf-8

# Provides a way to change the LED color of a BlinkStick USB device
# By Shervin Emami (shervin.emami@gmail.com), Jan 2024


# For compatibility with other projects
GRAMMAR_MODE = "Normal"
ENABLE_BLINKSTICK = True


if ENABLE_BLINKSTICK:
    try:
        from blinkstick import blinkstick
        bstick = blinkstick.find_first()
        if bstick:
            print("Found BlinkStick USB LED", bstick.get_serial())
        else:
            print("Error: Couldn't access the BlinkStick USB LED")
    except:
        bstick = None

# Show the current mode, using the USB LED
# args can be 'off', 'on', 'disabled' or 'sleeping'.
def updateLED(args, grammarMode = "Normal"):
    if ENABLE_BLINKSTICK:
        try:
            #print("In updateLED ", args, grammarMode)
            if bstick:
                V = 5  # LED Brightness upto 255
                if args == "on":
                    # Set my BlinkStick LED to green (ON, Normal mode) or blue (ON, Command mode)
                    if grammarMode == "Normal" and GRAMMAR_MODE == "Normal":
                        bstick.set_color(red=0, green=V, blue=0)
                    elif grammarMode == "Yellow":
                        bstick.set_color(red=V, green=V, blue=0)
                    elif grammarMode == "Pink":
                        bstick.set_color(red=V*1.2, green=V/3, blue=V/2.5)
                    elif grammarMode == "BlueGreen":
                        bstick.set_color(red=1, green=9, blue=3)
                    else:
                        bstick.set_color(red=0, green=0, blue=V*1.2)
                elif args == "disabled":
                    # Set my BlinkStick LED to red (disabled)
                    bstick.set_color(red=V*2, green=0, blue=0)
                elif args == "sleeping":
                    # Set my BlinkStick LED to purple (sleeping)
                    bstick.set_color(red=1, green=0, blue=0)
                elif args == "off":
                    # Set my BlinkStick LED to black (off)
                    bstick.set_color(red=0, green=0, blue=0)
        except:
            print("Warning: Couldn't access the BlinkStick USB LED")
            pass
