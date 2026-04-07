# -*- coding: utf-8 -*-
"""
PedalClass_JsonTest

Test a midipedal class and serialization to and from json

An instanace of the midipedal class will handle a single pedal
A list of midipedal objects will handle multiple pedals
The json configuration will allow a user to change the midi
output of the pedal with multiple banks of midi to pedal assignemts

Created on Fri Jan 23 13:36:29 2026

@author: skran
"""

import json
import io

class Stripper(io.RawIOBase):
    def __init__(self, base_stream):
        self.stream = base_stream
        self.buffer = bytearray()

    def readinto(self, b):
        # This is a simplified single-line comment (//) stripper
        line = self.stream.readline()
        if not line:
            return 0  # EOF
        
        # Strip C-style single line comments
        if b'//' in line:
            line = line.split(b'//')[0] + b'\n'
            
        n = len(line)
        b[:n] = line
        return n

    def readable(self):
        return True

def parse_json_with_comments(filepath):
    try:
        with open(filepath, "rb") as f:
            # Wrap the file stream in our stripper
            strip = Stripper(f)
            # Wrap the byte stream into a TextIOWrapper for the json parser
            text_stream = io.TextIOWrapper(strip)
            
            # json.load reads from the stream incrementally
            return json.load(text_stream)
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except json.JSONDecodeError:
        print(f"Could not decode JSON from {file_path}.")


def statusbytes(pedal):
    _statusbytes = []
    if pedal[0] == "NOTE":
        _statusbytes.append(0x90 + + pedal[4]) #Note on
        _statusbytes.append(0x80 + + pedal[4]) #Note off
    elif pedal[0] in ("CC","CT","CA"):
        _statusbytes.append(0xB0 + + pedal[4])
    elif pedal[0] == "PC":
        _statusbytes.append(0xC0 + + pedal[4])
    elif pedal[0] == "TR":
        _statusbytes.append(0xFA) #Start
        _statusbytes.append(0xFC) #Stop
        _statusbytes.append(0xFB) #Continue
        _statusbytes.append(0xFF) #Reset
    else:
        _statusbytes.append(0xFF)
    return _statusbytes

class midipedal:
    
    def fill_statusbytes(self):
        self._statusbytes = []
        if self.kind == "NOTE":
            self._statusbytes.append(0x90 + self.ch) #Note on
            self._statusbytes.append(0x80 + self.ch) #Note off
        elif self.kind in ("CC","CT","CA"):
            self._statusbytes.append(0xB0 + self.ch)
        elif self.kind == "PC":
            self._statusbytes.append(0xC0 + self.ch)
        elif self.kind == "TR":
            self._statusbytes.append(0xFA) #Start
            self._statusbytes.append(0xFC) #Stop
            self._statusbytes.append(0xFB) #Continue
            self._statusbytes.append(0xFF) #Reset
        else:
            self._statusbytes.append(0xFF)
        
    def __init__(self, kind, val, onvel, offvel, ch):        
        self.kind = kind
        self.val = val
        self.onvel = onvel
        self.offvel = offvel
        self.ch = ch
        self.io_value = 1 #Start with button up
        self.count = 0
        self.fill_statusbytes()
    
    def __repr__(self):
        cls_name = type(self).__name__
        return f"{cls_name}:{self.kind},{self.val},{self.onvel},{self.offvel},{self.ch};"
        
                    
    def assign(self, kind, val, onvel, offvel, ch):
        self.kind = kind
        self.val = val
        self.onvel = onvel
        self.offvel = offvel
        self.ch = ch
        self.io_value = 1 #Start with button up
        self.count = 0
        self.fill_statusbytes()

    def LED(self):
        return self.io_value
    
    def toggle(self):
        return self.count % 1
    
    def reset(self):
        self.state = 0
        
    def scaled(self, inval, high, low, maxval):
        return (self.inval * (high - low) / maxval) + low
    
    #NOTE: Call this before midi, if bankchange then no midi
    def bankchange(self,io_value):
        return self.value if self.kind == "BC" else 0

    #NOTE: Bank not processed in midi    
    def midi(self, io_value, max_value):

        #NOTE: button down is an io_value of 0
        if self.io_value != io_value and io_value == 0:
            self.count = self.count + 1
            self.io_value = io_value
        
        #NOTE: io_value == 0 means down, io_value != 0 means up
        #NOTE: toggle actions happen on button up, not down
        #NOTE: CA,CT only happens in 1st part (io_value == 0) of if
        #NOTE: BC inly happens in 2nd part of if
        #
        if io_value == 0 or self.kind in ("CA", "CT"):
            if self.kind == "NOTE":
                return bytes([self.statusbytes[0], self.val, self.onvel])
            elif self.kind == "CC":
                return bytes([self.statusbytes[0], self.val, self.onvel])
            elif self.kind == "CA":
                return bytes([self.statusbytes[0], self.val, 
                              self.scaled(self.inval, self.onvel, self.offvel, max_value)])
            elif self.kind == "CT":
                if self.toggle():
                    return bytes([self.statusbytes[0], self.val, self.onvel])
                else:
                    return bytes([self.statusbyte[0], self.val, self.offvel])                
            elif self.kind == "PC":
                return bytes([self.statusbytes[0], self.val])
            elif self.kind == "TR":
                return bytes([self.statusbytes[self.val]])
            else: 
                return bytes([0])
        else:
            if self.kind == "NOTE":
                return bytes([self.statusbytes[1], self.val, self.offvel])
            elif self.kind == "CC":
                return bytes([self.statusbyte, self.val, self.offvel])                
            else:
                return bytes([0]) #this means do nothing
            

#Recursively converts a nested list to a nested tuple.
#
def to_tuple(data):
    if isinstance(data, list):
        # Recursively apply to items and wrap in a tuple
        return tuple(to_tuple(item) for item in data)
    else:
        # Base case: item is not a list (int, string, etc.)
        return data

# 2 dimensional list for a bank
# Four Banks ((0-4), 
# Eight buttons + Volume Pedal (0-8)
bank_pedal_onoff = [
    [ # bank number 1
    midipedal("NOTE",0x01,0x7F,0x00,0x00),
    midipedal("NOTE",0x02,0x7F,0x00,0x00),
    midipedal("NOTE",0x03,0x7F,0x00,0x00),
    midipedal("NOTE",0x04,0x7F,0x00,0x00),
    midipedal("CC",  0x21,0x7F,0x00,0x00),
    midipedal("CT",  0x22,0x7F,0x00,0x00),
    midipedal("CA",  0x07,0x7F,0x00,0x00),
    midipedal("BC",  0x80,0x00,0x00,0x00),
    midipedal("BC",  0x81,0x00,0x00,0x00),
    ],
    [ # bank number 2
    midipedal("NOTE",0x01,0x7F,0x00,0x01),
    midipedal("NOTE",0x02,0x7F,0x00,0x01),
    midipedal("NOTE",0x03,0x7F,0x00,0x01),
    midipedal("NOTE",0x04,0x7F,0x00,0x01),
    midipedal("CC",  0x21,0x7F,0x00,0x01),
    midipedal("CT",  0x22,0x7F,0x00,0x01),
    midipedal("CA",  0x07,0x7F,0x00,0x01),
    midipedal("BC",  0x80,0x00,0x00,0x01),
    midipedal("BC",  0x81,0x00,0x00,0x01),
    ],
    [ # bank number 3
    midipedal("NOTE",0x01,0x7F,0x00,0x02),
    midipedal("NOTE",0x02,0x7F,0x00,0x02),
    midipedal("NOTE",0x03,0x7F,0x00,0x02),
    midipedal("NOTE",0x04,0x7F,0x00,0x02),
    midipedal("CC",  0x21,0x7F,0x00,0x02),
    midipedal("CT",  0x22,0x7F,0x00,0x02),
    midipedal("CA",  0x07,0x7F,0x00,0x02),
    midipedal("BC",  0x80,0x00,0x00,0x02),
    midipedal("BC",  0x81,0x00,0x00,0x02),
    ],
    [ # bank number 4
    midipedal("NOTE",0x01,0x7F,0x00,0x03),
    midipedal("NOTE",0x02,0x7F,0x00,0x03),
    midipedal("NOTE",0x03,0x7F,0x00,0x03),
    midipedal("NOTE",0x04,0x7F,0x00,0x03),
    midipedal("CC",  0x21,0x7F,0x00,0x03),
    midipedal("CT",  0x22,0x7F,0x00,0x03),
    midipedal("CA",  0x07,0x7F,0x00,0x03),
    midipedal("BC",  0x80,0x00,0x00,0x03),
    midipedal("BC",  0x81,0x00,0x00,0x03),
    ]
]

def pedal_serializer(obj):
    if isinstance(obj, midipedal):
        return obj.__dict__
    raise TypeError("Type not serializable")


#code to create an initial file format from the object definition
in_json_string = json.dumps(bank_pedal_onoff, indent=4, default=pedal_serializer)
loaded_json = json.loads(in_json_string)

#pretty_json_string = json.dumps(loaded_json, indent=4, default=pedal_serializer)
#print(pretty_json_string)

print(loaded_json[0][0]["kind"])
print(loaded_json[0][0]["val"])
print(loaded_json[0][0]["onvel"])
print(loaded_json[0][0]["offvel"])
print(loaded_json[0][0]["ch"])

file_path = "midi_pedal.json"

"""
# --- Serialization: Write to a file ---
try:
    with open(file_path, 'w') as json_file:
        # The json.dump() function writes the Python object to the file
        json.dump(loaded_json, json_file, indent=4)
    print(f"Data successfully serialized and written to {file_path}")
except IOError as e:
    print(f"Error writing file: {e}")

print(os.getcwd())
"""

file_path = "midi_pedal_view.json"

loaded_from_file = parse_json_with_comments(file_path)
loaded_tuple = to_tuple(loaded_from_file)

del loaded_from_file

DOWN = 0
UP = 1

KIND = 0
VAL = 1
ONVEL = 2
OFFVEL = 3
CH = 4

m_bank = 0
m_pedal = 0

a_pedal = loaded_tuple[m_bank][m_pedal]

print(loaded_tuple)

print("# OF BANKS:",len(loaded_tuple))
print("KIND:", a_pedal[KIND])
print("VAL:", a_pedal[VAL])
print("ONVEL:", a_pedal[ONVEL])
print("OFFVEL:", a_pedal[OFFVEL])
print("CH:", a_pedal[CH]) #ch

print("STATUSBYTES:",statusbytes(a_pedal))

#list of pedals
def make_pedal_objects(banks,bank):
    build = []
    for i in banks[bank]:
        build.append(midipedal(i[KIND],i[VAL],i[ONVEL],i[OFFVEL],i[CH]))
    return build

def assign_pedal_objects_bank(pedals,banks,bank):
    for i, p in zip(banks[bank], pedals):
        p.assign(i[KIND],i[VAL],i[ONVEL],i[OFFVEL],i[CH])
 
#
pedal_objects = make_pedal_objects(loaded_tuple,0)

print("Bank #0")
print(loaded_tuple[0])
print("Pedals")
print(pedal_objects)

assign_pedal_objects_bank(pedal_objects,loaded_tuple,1)

print("Bank #1")
print(loaded_tuple[1])
print("Pedals")
print(pedal_objects)
