# -*- coding: utf-8 -*-
"""

@author: Steven Kraninger

Main code file for MIDI pedal board project

This code initializes the MIDI pedal board,
 sets up the neopixel LEDs,
 and runs the main loop to handle button presses,
 volume pedal changes, and MIDI events.

"""
#
import board
import keypad
import neopixel_write
import digitalio
import analogio
import time
import json
import usb_midi
import gc

import MidiPedal as mp
import PedalLeds as pl


# ANALOG INPUT CONSTANTS
PEDALMAXVALUE = 65535

#IO CONFIGURATION

# Initialize the pin for output
PIXEL_PIN = board.GP28
pixelpin = digitalio.DigitalInOut(PIXEL_PIN)
pixelpin.direction = digitalio.Direction.OUTPUT

midi_in = usb_midi.ports[0]
midi_out = usb_midi.ports[1]
analog_in = analogio.AnalogIn(board.A0)

# KEYPAD NEOPIXEL TEST
keys = keypad.Keys(
    (board.GP2, board.GP3, board.GP4, board.GP5, 
     board.GP6, board.GP7, board.GP8, board.GP9),
    value_when_pressed=False,
    pull=True
)

# NEOPIXEL CHASE
DURATION = 4                    # Total run time in seconds
CHASE_SPEED = 0.1               # Delay between movement

def color_chase(leds):

    #print("Starting color chase with neopixel_write...")
    start_time = time.monotonic()
    colorindex = 0

    while time.monotonic() - start_time < DURATION:
        for i in range(leds.numpixels):

            # Set the current pixel to red (G, R, B)           
            colorindex = leds.fill_chase_buffer(colorindex)
            # Write the entire buffer to the pin
            neopixel_write.neopixel_write(pixelpin, leds.pixelbuffer)
            time.sleep(CHASE_SPEED)
            
            if time.monotonic() - start_time >= DURATION:
                break

    # Turn off all pixels when finished
    leds.resetpixelbuffer()
    neopixel_write.neopixel_write(pixelpin, leds.resetpixelbuffer())
    #print("Neopixels Done!")

def midipedal_loop(leds, banks):

    pedals = banks.pedals()

    leds.clear_pedal_buffers()
    leds.bankchange(banks.bankno, pedals)

    analogpedal = banks.analogpedal()

    #all the object setup is done
    # collect garbage to free up memory before we start the loop
    gc.collect()

    #only send if CC value changes
    cc_value = -1
    last_cc_value = -1

    io_value = mp.UP

    #set up for smoothing the analog input
    raw_value = -1
    last_raw_value = analog_in.value

    while True:

        ################
        # Button presses
        #
        event = keys.events.get()

        if event:
            #print(f"Button {event.key_number} {'pressed' if event.pressed else 'released'}")
            idx = event.key_number

            if event.pressed:
                io_value = mp.DOWN
            else:
                io_value = mp.UP

            pedal = pedals[idx]

            if pedal.bankchange(banks, io_value):
                pedals = banks.pedals()
                #pedals allow us to remember toggled leds
                leds.bankchange(banks.bankno, pedals)

            elif pedal.hasmidi(io_value):
                #print(f"Pedal hasmidi {idx} iovalue {io_value}")
                midi_out.write(pedal.midi(io_value))

            else:
                pedals[idx].set_io_state(io_value)

            leds.pedalchange(idx, pedal.ledstate)

        ################
        # Volume pedal
        #
        #Smooth analog_in.value by averaging with the last reading to reduce noise
        raw_value = (analog_in.value + last_raw_value) / 2
        last_raw_value  = raw_value

        #NOTE: The actual value for a pi pico is 0-4096, mapped by circuitpython to 0-65535
        # and the cc_value is 0-127, so scale it ...
        cc_value = analogpedal.CCanalog(raw_value, PEDALMAXVALUE)
        if cc_value != last_cc_value:
            midi_out.write(cc_value)
            last_cc_value = cc_value

        ################
        # Midi in events
        #
        msg = midi_in.read(3)
        if msg is not None and len(msg) == 3:
            #print(f"MIDI message received: {msg}")
            leds.midiin(msg)
    
        #Neopixel updates
        if leds.changed:
            # Write the entire buffer to the pin
            neopixel_write.neopixel_write(pixelpin, leds.neopixelbuffer())

        time.sleep(0.01) # Small delay for stability

file_path = "midibanks.json"

pedalbanks = mp.midipedalbanks(file_path)
leds = pl.pedalleds()

color_chase(leds)
midipedal_loop(leds, pedalbanks)
