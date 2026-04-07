# -*- coding: utf-8 -*-
"""

@author: skran
"""

class pedalleds:
    
    def __init__(self):
        self.numpixels = 8
        self.pixelpin = None
        self.MAXCOLOR = 0xFF
        self.GREEN = bytearray((self.MAXCOLOR,0,0))
        self.BLUE = bytearray((0,self.MAXCOLOR,0))
        self.RED = bytearray((0,0,self.MAXCOLOR))
        self.OFF = bytearray((0,0,0))
        self.BANKCOLOR = self.BLUE
        self.PEDALCOLOR = self.RED
        self.RGB = [self.GREEN, self.RED, self.BLUE]
        self.bankled = 0x00
        self.pedalleds = [self.OFF.copy()] * 8
        self.midileds = [self.OFF.copy()] * 8
        self.pixelbuffer = bytearray(self.numpixels * 3)
        self.chasecolor = 0
        self.changed = False
        
    def clear_pixelbuffer(self):
        for i in range(len(self.pixelbuffer)):
            self.pixelbuffer[i] = 0
        self.changed = True

    def clear_pedal_buffers(self):
        self.bankled = 0x00
        for i in range(self.numpixels):
            self.pedalleds[i] = self.OFF.copy()
        for i in range(self.numpixels):
            self.midileds[i] = self.OFF.copy()
        self.changed = True

    def fill_chase_buffer(self, colorindex):
        for i in range(self.numpixels):
            colorindex = self.chasecolor % 3
            self.chasecolor = self.chasecolor + 1
            self.pixelbuffer[i * 3] = self.RBG[colorindex][0]
            self.pixelbuffer[i * 3 + 1] = self.RBG[colorindex][1]
            self.pixelbuffer[i * 3 + 2] = self.RBG[colorindex][2]
        self.changed = True
        
    def set_pixel(self, pixelno, color):
        self.midileds[pixelno] = color
        self.changed = True
            
    def get_pixel(self, pixelno):
        return self.midileds[pixelno]

    def mask_pixel(self, pixelno, color, coloradd):
        c = self.midileds[pixelno]
        c[0] = (c[0] & ~ color[0]) + coloradd[0]
        c[1] = (c[1] & ~ color[1]) + coloradd[1]
        c[2] = (c[2] & ~ color[2]) + coloradd[2]
        return c
    
    def color_b(self,color, bright):
        c = bytearray((color[0]*bright, color[1]*bright,color[2]*bright))
        return c
    
    def midiin(self, status, note_num, velocity):
        #Processes incoming MIDI notes and updates NeoPixel colors/octaves
        pixel = 0
        rgb = 0
        
        #Pixel number logic
        if 60 <= note_num <= 71:
            pixel = note_num - 60
            rgb = 0
        elif 72 <= note_num <= 83:
            pixel = note_num - 72
            rgb = 1
        elif 84 <= note_num <= 95:
            rgb = 2
            pixel = note_num - 84
        else:
            #Nothing going to happen here ...
            return

        #NOTE: Color masking, 0=GREEN,1=BLUE,2=RED, MAXCOLOR=255
        
        if (status & 0xF0) == 0x90 and velocity > 0:
            brightness = velocity / 127.0
            
            color = self.midileds[pixel]
            color[rgb] = (color[rgb] & ~ self.MAXCOLOR) + round(self.MAXCOLOR * brightness)
                
            # For testing, we update the first NeoPixel/Virtual LED
            self.set_pixel(pixel, color)
            
        elif (status & 0xF0) == 0x80 or ((status & 0xF0) == 0x90 and velocity == 0):

            color = self.midileds[pixel]
            color[rgb] = (color[rgb] & ~ self.MAXCOLOR)
            
            self.set_pixel(pixel, color)

    def pedalchange(self, pedalno, pedalstate):
        if pedalstate == 0:
            self.pedalleds[pedalno] = self.OFF.copy()
        else:
            self.pedalleds[pedalno] = self.PEDALCOLOR.copy()
        self.changed = True
        
    def bankchange(self, bankno):
        self.bankled = bankno
        self.changed = True

    def neopixelbuffer(self):
        #all pixels OFF
        self.clear_pixelbuffer()
        
        for i in range(self.numpixels):
            midiled = self.midileds[i]
            if midiled != self.OFF:
                #midi lighting the pixel
                self.pixelbuffer[i * 3] = midiled[0]
                self.pixelbuffer[i * 3 + 1] = midiled[1]
                self.pixelbuffer[i * 3 + 2] = midiled[2]            
            else:
                pedalled = self.pedalleds[i]
                if i == self.bankled:
                    #bank and pedal lighting one pixel
                    self.pixelbuffer[i * 3] = self.BANKCOLOR[0] + pedalled[0]
                    self.pixelbuffer[i * 3 + 1] = self.BANKCOLOR[1] + pedalled[1]
                    self.pixelbuffer[i * 3 + 2] = self.BANKCOLOR[2] + pedalled[2]
                else:
                    #pedal lighting the pixel
                    self.pixelbuffer[i * 3] = pedalled[0]
                    self.pixelbuffer[i * 3 + 1] =  pedalled[1]
                    self.pixelbuffer[i * 3 + 2] =  pedalled[2]
        self.changed = False
        return self.pixelbuffer   
            