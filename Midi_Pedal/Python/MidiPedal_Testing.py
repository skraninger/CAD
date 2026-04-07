# -*- coding: utf-8 -*-
"""

@author: skran
"""

import MidiPedal
import PedalLeds

"""
try:
    if sys.platform == "microcontroller":
        import board
        import usb_midi
        import keypad
        import neopixel
        import analogio
    else:
        raise ImportError
except (ImportError, AttributeError):
    print("Import Error")
"""

"""    
#mocking class midi_out
class midi_out:
    def __init__(self):
        self.foo = ""
                                
    def write(self,bytes):
        print(bytes)
        
#mocking classe keys
class keys:
    class event:
        def get(self):
            return self
        def __init__(self):        
            self.pressed = True
            self.idx = 1
"""

# TESTING FOR MidiPedal class

PEDALMAXVALUE = 65535

file_path = "midibanks.json"

pedalbanks = MidiPedal.midipedalbanks(file_path)
print("# OF BANKS:", pedalbanks.bankmax)
print("BANK:", pedalbanks.bankno)


pedal = pedalbanks.pedals()[0]
print("KIND:", pedal.kind)
print("VAL:", pedal.val)
print("ONVEL:", pedal.onvel)
print("OFFVEL:", pedal.offvel)
print("CH:", pedal.ch)
print("MIDI:", pedal._midi)
print("MIDI DOWN:", pedal.midi(MidiPedal.DOWN))
print("MIDI UP:", pedal.midi(MidiPedal.UP))

pedal = pedalbanks.analogpedal()

print("KIND:", pedal.kind)
print("VAL:", pedal.val)
print("ONVEL:", pedal.onvel)
print("OFFVEL:", pedal.offvel)
print("CH:", pedal.ch)
print("MIDI:", pedal._midi)
print("MIDI DOWN:", pedal.midi(MidiPedal.DOWN))
print("MIDI UP:", pedal.midi(MidiPedal.UP))
print("MIDI ANALOG:", pedal.CCanalog(1000,PEDALMAXVALUE))

pedalbanks.nextbank()
print("BANK:", pedalbanks.bankno)

pedal = pedalbanks.pedals()[0]

print("KIND:", pedal.kind)
print("VAL:", pedal.val)
print("ONVEL:", pedal.onvel)
print("OFFVEL:", pedal.offvel)
print("CH:", pedal.ch)
print("MIDI:", pedal._midi)
print("MIDI DOWN:", pedal.midi(MidiPedal.DOWN))
print("MIDI UP:", pedal.midi(MidiPedal.UP))

pedalbanks.nextbank()
pedal = pedalbanks.pedals()[0]

print("KIND:", pedal.kind)
print("VAL:", pedal.val)
print("ONVEL:", pedal.onvel)
print("OFFVEL:", pedal.offvel)
print("CH:", pedal.ch)
print("MIDI:", pedal._midi)
print("MIDI DOWN:", pedal.midi(MidiPedal.DOWN))
print("MIDI UP:", pedal.midi(MidiPedal.UP))

#TESTING FOR pedalleds CLASS

leds = PedalLeds.pedalleds()

leds.clear_pixelbuffer()
leds.clear_pedal_buffers()

print("LEDS: Initial")
print(leds.neopixelbuffer())

print("LEDS: pedalchange")
leds.pedalchange(0,1)
print(leds.neopixelbuffer())

print("LEDS: bankchange")
leds.bankchange(3)
print(leds.neopixelbuffer())
leds.bankchange(3)
print(leds.neopixelbuffer())

print("LEDS: midiin")
leds.midiin(0x90, 60, 65)
print(leds.neopixelbuffer())
leds.midiin(0x90, 72,127)
print(leds.neopixelbuffer())
        
        
"""
if not IS_DESKTOP:
    midi_in = usb_midi.ports[0]
    midi_out = usb_midi.ports[1]
    pixels = neopixel.NeoPixel(board.NEOPIXEL, 8, brightness=0.5, auto_write=True)
    pixels.fill(INITIAL_COLOR)
    potentiometer = analogio.AnalogIn(board.A0)
    button_pins = (board.GP0, board.GP1, board.GP2, board.GP3,
                   board.GP4, board.GP5, board.GP6, board.GP7)
    keys = keypad.Keys(button_pins, value_when_pressed=False, pull=True)
"""


"""
# --- HELPER FUNCTIONS ---
def send_raw_midi(status, data1, data2):
    midi_out.write(bytearray([status, data1, data2]))

def set_pixel_color(index, color):
    pixels[index] = color

def handle_incoming_midi(status, note_num, velocity):
    #Processes incoming MIDI notes and updates NeoPixel colors/octaves

    #Pixel number logic
    if 60 <= note_num <= 71:
        pixel = note_num - 60
    elif 72 <= note_num <= 83:
        pixel = note_num - 72
    elif 84 <= note_num <= 95:
        pixel = note_num - 84
    else:
        pixel = 0

    if (status & 0xF0) == 0x90 and velocity > 0:
        brightness = velocity / 127.0
        
        # Color logic: Middle C Octave (60-71) = Red, Next (72-83) = Blue, Next (84-95) = Red
        if 60 <= note_num <= 71:
            color = (int(255 * brightness), 0, 0)
        elif 72 <= note_num <= 83:
            color = (0, 0, int(255 * brightness))
        elif 84 <= note_num <= 95:
            color = (0,int(255 * brightness), 0)            
        else:
            color = INITIAL_COLOR
            
        # For testing, we update the first NeoPixel/Virtual LED
        set_pixel_color(pixel, color)
        
    elif (status & 0xF0) == 0x80 or ((status & 0xF0) == 0x90 and velocity == 0):
        set_pixel_color(pixel, INITIAL_COLOR)

def update_midi_logic():
    global last_midi_volume
    global pedals
    global banks
    global bankno
    
    event = keys.events.get()

    if event:
        idx = event.key_number
        io_value = event.pressed if 0 else 1
        pedal = pedals[idx]

        if pedal.bankchange():
            if pedal.val == BANK_UP:
                bankno = (bankno == bankmax) if 0 else bankno + 1
            elif pedal.val == BANK_DOWN:
                bankno = (bankno == 0) if bankmax else bankno - 1
            pedals = banks[bankno]
        elif pedal.hasmidi(io_value):
            midi_out.write(pedal.midi_out(io_value))
"""

"""
    leds.pedalchange(pedal)

    if volume.change(potentiometer.value):
        midi_out.write(pedals.CCanalog(volume.value, volume.max))
 
    msg = midi_in.read(3)
    if msg is not None and len(msg) == 3:	
    	leds.midiin(msg)
    
    if leds.changed():
    	leds.writepixels()
"""

