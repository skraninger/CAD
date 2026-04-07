# -*- coding: utf-8 -*-
"""

@author: skran

PelalLeds class
Controls the NeoPixel LEDs on the MIDI pedal board
Bank LEDs are blue, Pedal LEDs are green, MIDI LEDs can be any color

"""
#Bank UP/DOWN values
BANK_UP = 0xFF
BANK_DOWN = 0xFE
MAXCOLOR = 0xFF
MAXBANKS = 16
MAXLEDS = 8

GREEN = bytearray((MAXCOLOR,0,0))
RED = bytearray((0,MAXCOLOR,0))
BLUE = bytearray((0,0,MAXCOLOR))
OFF = bytearray((0,0,0))

#sequence to light pedal pixels, 0-3 map to 0-3, 4-7 map to 7-4
PEDALPIXELMAP = (0, 1, 2, 3, 7 , 6, 5, 4)

#bank pixels should follow the sequence 7, 6, 5, 4, 0, 1, 2, 3 
BANKPIXELMAP = (7, 6, 5, 4, 0, 1, 2, 3)

class pedalleds:
    
    def __init__(self):
        self.numpixels = MAXLEDS
        self.pixelpin = None
        #Neopixes are GRB, so we define the colors as bytearrays for easy manipulation
        #self.GREEN = bytearray((MAXCOLOR,0,0))
        #self.RED = bytearray((0,MAXCOLOR,0))
        #self.BLUE = bytearray((0,0,MAXCOLOR))
        #self.OFF = bytearray((0,0,0))
        self.BANKCOLOR_1 = BLUE
        self.BANKCOLOR_2 = GREEN
        self.PEDALCOLOR = RED
        self.CHASECOLOR = [RED, RED, RED, GREEN, GREEN, GREEN, BLUE, BLUE, BLUE]
        #only one bank can be active at a time, so we track it with a single variable
        
        self.bankled = BANKPIXELMAP[0]

        #pedals can only be on or off
        self.pedalleds = [0] * MAXLEDS

        #NOTE: this syntax prevents refrence to the same bytearray
        # and creates a new one for each entry
        # Midi based values can be any color, so we initialize them to off
        self.midileds = [bytearray(OFF) for _ in range(MAXLEDS)]

        #pixelbuffer is the buffer we will write to the neopixels,
        #  it combines bank, pedal and midi states
        self.pixelbuffer = bytearray(self.numpixels * 3)
        self.chasecolor = 0
        self.changed = False
        
    def clear_pixelbuffer(self):
        for i in range(len(self.pixelbuffer)):
            self.pixelbuffer[i]
        self.changed = True

    def clear_pedal_buffers(self):
        self.bankled = 0x00
        for i in range(self.numpixels):
            self.pedalleds[i] = 0
            self.midileds[i][0] = 0x00
            self.midileds[i][1] = 0x00
            self.midileds[i][2] = 0x00
        self.changed = True

    def fill_chase_buffer(self, colorindex):
        for i in range(self.numpixels):
            j = BANKPIXELMAP[i]
            colorindex = self.chasecolor % len(self.CHASECOLOR)
            self.chasecolor = self.chasecolor + 1
            self.pixelbuffer[j * 3] = self.CHASECOLOR[colorindex][0]
            self.pixelbuffer[j * 3 + 1] = self.CHASECOLOR[colorindex][1]
            self.pixelbuffer[j * 3 + 2] = self.CHASECOLOR[colorindex][2]
        self.changed = True
        return colorindex
    
    def set_pixel(self, pixelno, color):
        self.midileds[pixelno][0] = color[0]
        self.midileds[pixelno][1] = color[1]
        self.midileds[pixelno][2] = color[2]    
        self.changed = True
            
    def get_pixel(self, pixelno):
        return self.midileds[pixelno]

    def midiin(self, msg):
        #Processes incoming MIDI notes and updates NeoPixel colors/octaves
        pixel = 0
        rgb = 0
        
        status = msg[0]
        note_num = msg[1]
        velocity = msg[2]

        #print(f"MIDI IN: status={status:X}, note={note_num}, velocity={velocity}")

        #skip non-note events
        if (status & 0xF0) != 0x90 and (status & 0xF0) != 0x80:
            return

        #Pixel number logic
        if 60 <= note_num <= 67:
            pixel = note_num - 60
            rgb = 0
        elif 72 <= note_num <= 79:
            pixel = note_num - 72
            rgb = 1
        elif 84 <= note_num <= 91:
            rgb = 2
            pixel = note_num - 84
        else:
            #print(f"Note {note_num} out of MIDI LED range, ignoring")
            return

        #rotate pixel numbers to account for physical layout
        #map pedal location to matching pixel location, 0-3 map to 0-3, 4-7 map to 7-4
        pixel = PEDALPIXELMAP[pixel] 

        #print(f"MIDI mapped to pixel {pixel}, color index {rgb}")

        #NOTE: Color masking, 0=RED,1=GREEN,2=BLUE, MAXCOLOR=255
        
        if (status & 0xF0) == 0x90 and velocity > 0:
            brightness = velocity / 127.0
            
            color = self.midileds[pixel]
            #print(f"Pixel {pixel} is color {color} {color[0]} {color[1]} {color[2]}")   
            color[rgb] = round(MAXCOLOR * brightness)
            #print(f"Color after set {color} {color[0]} {color[1]} {color[2]}")   
            #print(f"Setting pixel {pixel} to color {color} based on MIDI velocity {velocity}")
            self.set_pixel(pixel, color)
            
        elif (status & 0xF0) == 0x80 or ((status & 0xF0) == 0x90 and velocity == 0):
            color = self.midileds[pixel]
            #print(f"Clearing pixel {pixel} color {color} in MIDI off event")
            color[rgb] = 0x00
            self.set_pixel(pixel, color)

    def pedalchange(self, pedalno, pedalstate):
        #print(f"Pedal {pedalno} state changed to {pedalstate}")
        ledno = PEDALPIXELMAP[pedalno]

        if self.pedalleds[ledno] != pedalstate:
            self.pedalleds[ledno] = pedalstate
            self.changed = True
        
    def bankchange(self, bankno, pedals):
        #print(f"Leds bank changed to {bankno}")        
        if self.bankled != bankno:
            self.bankled = bankno % MAXBANKS
            #set leds based on pedals for this bank
            for p in range(len(self.pedalleds)):
                self.pedalleds[p] = pedals[PEDALPIXELMAP[p]].ledstate   
            self.changed = True

    def neopixelbuffer(self):

        #allow for up to 16 banks, 8 in one color
        if self.bankled >= MAXLEDS:
            bankcolor = self.BANKCOLOR_2
            self.bankled = self.bankled % MAXLEDS
            bankpixelmapped = BANKPIXELMAP[self.bankled]
        else:
            bankpixelmapped = BANKPIXELMAP[self.bankled]
            bankcolor = self.BANKCOLOR_1

        #all pixels OFF
        self.clear_pixelbuffer()
        
        for i in range(self.numpixels):

            midiled = self.midileds[i]

            #print(f"Midleds {self.midileds}")
            #print(f"Pixel {i} MIDI LED state: {midiled}")

            if midiled[0] != 0 or midiled[1] != 0 or midiled[2] != 0:
                #print(f"Pixel {i} MIDI color: {midiled}")
                self.pixelbuffer[i * 3] = midiled[0]
                self.pixelbuffer[i * 3 + 1] = midiled[1]
                self.pixelbuffer[i * 3 + 2] = midiled[2]            
            else:
                self.pixelbuffer[i * 3] = OFF[0]
                self.pixelbuffer[i * 3 + 1] = OFF[1]
                self.pixelbuffer[i * 3 + 2] = OFF[2]

                if i == bankpixelmapped:
                    #print(f"Pixel {i} Bank color: {self.BANKCOLOR}")
                    self.pixelbuffer[i * 3] = bankcolor[0]
                    self.pixelbuffer[i * 3 + 1] = bankcolor[1]
                    self.pixelbuffer[i * 3 + 2] = bankcolor[2] 

                #print(f"Pixel {i} Pedal state: {self.pedalleds[i]}")

                if self.pedalleds[i] != 0:
                    #pedal lighting the pixel
                    self.pixelbuffer[i * 3] = +self.PEDALCOLOR[0]
                    self.pixelbuffer[i * 3 + 1] += self.PEDALCOLOR[1]
                    self.pixelbuffer[i * 3 + 2] += self.PEDALCOLOR[2]

        self.changed = False
        return self.pixelbuffer 

    def resetpixelbuffer(self):
        self.clear_pixelbuffer()
        self.changed = False
        return self.pixelbuffer