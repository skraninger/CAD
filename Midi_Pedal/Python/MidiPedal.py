# -*- coding: utf-8 -*-
"""

@author: skran

MidiPedal class

Load a JSON definition file
To create a list of MidiPedal Banks
That contain a list of MidiPedal objects

"""

import json

#CONSTANT Definitions

#Indexes into json read pedal array
KIND = 0
VAL = 1
ONVEL = 2
OFFVEL = 3
CH = 4

#Pedal UP/DOWN values
DOWN = 0
UP = 1

#MIDI packet bytes
STATUS_BYTE = 0
VAL_BYTE = 1

#Bank UP/DOWN values
BANK_UP = 0xFF
BANK_DOWN = 0xFE


class midipedal:
    
    def fill_midi(self):
        self._midi = []
        if self.kind == "NOTE":
            self._midi.append((0x90 + self.ch, self.val, self.onvel)) #Note on
            self._midi.append((0x80 + self.ch, self.val, self.offvel)) #Note off
        elif self.kind in ("CC","CT","CA"):
            self._midi.append((0xB0 + self.ch, self.val, self.onvel))
            self._midi.append((0xB0 + self.ch, self.val, self.offvel))
        elif self.kind == "PC":
            self._midi.append((0xC0 + self.ch, self.val))
        elif self.kind == "TR":
            if self.val == 1:
                self._midi.append((0xFA)) #Start
            elif self.val == 2:
                self._midi.append((0xFC)) #Stop
            elif self.val == 3:
                self._midi.append((0xFB)) #Continue
            else:
                self._midi.append((0xFF)) #Reset
        else:
            self._midi.append((0xFF))
        
    def __init__(self, kind, val, onvel, offvel, ch):        
        self.kind = kind
        self.val = val
        self.onvel = onvel
        self.offvel = offvel
        self.ch = ch
        self.io_value = 1 #Start with button up
        self.count = 0
        self._midi = []
        self.fill_midi()
    
    def __repr__(self):
        cls_name = type(self).__name__
        return f"{cls_name}:{self.kind},{self.val},{self.onvel},{self.offvel},{self.ch};"
                            
    def reset(self):
        self.io_value = 1
        self.count = 0
        
    def LED(self):
        return self.io_value
    
    def toggle(self):
        return self.count % 1
            
    def scaled(self, inval, high, low, maxval):
        return round((inval * (high - low) / maxval) + low)
    
    #NOTE: Call this before midi, if bankchange then no midi
    def bankchange(self,io_value):
        return self.kind == "BC"

    #NOTE: Has Midi, if event is DOWN always
    #   if event is UP, needs 2 elements in _midi
    def hasmidi(self, io_value):
        if io_value == DOWN:
            return True
        else:
            return len(self._midi) > 1
        
    #NOTE: Bank not processed in midi    
    def midi(self, io_value):

        #NOTE: button down is an io_value of 0
        if self.io_value != io_value and io_value == DOWN:
            self.count = self.count + 1
            self.io_value = io_value
        
        #NOTE: io_value == 0 means down, io_value != 0 means up
        #NOTE: toggle actions happen on button up, not down
        #NOTE: CT only happens in 1st part (io_value == 0) of if
        #NOTE: BC inly happens in 2nd part of if
        #NOTE: CA is handled with ccanalog
        #
        if io_value == DOWN or self.kind == "CT":
            if self.kind == "CT":
                if self.toggle():
                    return bytes(self._midi[DOWN])
                else:
                    return bytes(self._midi[UP])                
            else: 
                return bytes(self._midi[DOWN])
        else:
            return bytes(self._midi[UP])
    
    #NOTE: CA is an analog pedal
    def isccanalog(self):
        return self.kind == "CA"
    
    #NOTE: CA velocity is replaced with the analog invalue <= maxvalue
    def CCanalog(self, invalue, maxvalue):
        #_midi bytes array
        # [0][0] is status byte for down press,
        # [0][1] is channel byte for down press
        return bytes((self._midi[DOWN][STATUS_BYTE], self._midi[DOWN][VAL_BYTE], 
            self.scaled(invalue, self.onvel, self.offvel, maxvalue)))


class midipedalbanks:

    def __init__(self, filename):
        self.banks = []
        self.bankno = 0
        self.bankmax = 0
        self.analogpedals = []
        
        self.load_json(filename)
        
    def load_json(self, filename="midibanks.json"):

        cleaned_lines = []
        
        try:
            # Open the file for reading
            with open(filename, "r") as f:
                for line in f:
                    # Split at the comment marker and take the part before it
                    # then strip whitespace to see if the line is still useful
                    clean_line = line.split("//")[0].strip()
                    
                    # Only keep the line if it's not empty after stripping
                    if clean_line:
                        cleaned_lines.append(clean_line)
            
            # Reconstruct the string from cleaned lines
            json_string = "".join(cleaned_lines)
            
            # Use json.loads() to convert the string into a Python object
            # This function deserializes the string into a dictionary or list
            data = json.loads(json_string)
        except OSError:
            data = [[]] #no data if error
            print("Error: Could not find or open the file.")
        except ValueError as e:
            data = [[]] #no data if error
            print(f"Error: Invalid JSON syntax after removing comments: {e}")

        #build list of banks
        self.banks = []
        #NOTE: only one analog pedal per bank
        self.analogpedals = []
        for b in data:
            #build list of midipedals
            bank = []
            analogpedal = None
            for p in b:
                if p[KIND] == "CA":
                    #analog pedal
                    analogpedal = midipedal(p[KIND],p[VAL],p[ONVEL],p[OFFVEL],p[CH])
                else:
                    bank.append(midipedal(p[KIND],p[VAL],p[ONVEL],p[OFFVEL],p[CH]))
            self.analogpedals.append(analogpedal)
            self.banks.append(bank)
        
        del cleaned_lines
        del data
        
        self.bankno = 0
        self.bankmax = len(self.banks)

    def nextbank(self):
        self.bankno += 1
        if self.bankno > self.bankmax:
            self.bankno = 0

    def priorbank(self):
        self.bankno -= 1
        if self.bankno < 0:
            self.bankno = self.bankmax
        
    def setbank(self, bank):
        if bank < 0:
            self.bankno = self.bankmax
        elif bank > self.bankmax:
            self.bankno = 0
        else:
            self.bankno = bank
        
    def pedals(self):
        return self.banks[self.bankno]

    def analogpedal(self):
        return self.analogpedals[self.bankno]
        
#Recursively converts a nested list to a nested tuple.
#
def to_tuple(data):
    if isinstance(data, list):
        # Recursively apply to items and wrap in a tuple
        return tuple(to_tuple(item) for item in data)
    else:
        # Base case: item is not a list (int, string, etc.)
        return data

def pedal_serializer(obj):
    if isinstance(obj, midipedal):
        return obj.__dict__
    raise TypeError("Type not serializable")

