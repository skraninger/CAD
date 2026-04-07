# -*- coding: utf-8 -*-
"""
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


class midipedal:
    
    _statusbyte = 0x00
    
    def __init__(self, kind, val, tog, vel, ch, bank):        
        self.kind = kind
        self.val = val
        self.tog = tog
        self.vel = vel
        self.ch = ch
        self.bank = bank
        self.state = 0
    
    def __repr__(self):
        cls_name = type(self).__name__
        return f"{cls_name}:{self.kind},{self.val},{self.tog},{self.vel},{self.ch},{self.bank};"
        
                    
    def assign(self, kind, val, tog, vel, ch, bank):
        self.kind = kind
        self.val = val
        self.tog = tog
        self.vel = vel
        self.ch = ch
        self.bank = bank
        self.state = 0

    def onoff(self):
        return self.state % 1
    
    def reset(self):
        self.state = 0
        
    def midi(self,invalue):
        #NOTE: invalue of 0 means to use toggle value
        if self.kind == "CCR":
            return bytes([self.statusbyte, self.val, self.vel])
        elif invalue != 0 or self.tog == 0xFF:
            return bytes([self.statusbyte, self.val, self.vel])
        else: 
            return bytes([self.statusbyte, self.tog, self.vel])

    def statusbyte(self):
        if self.kind == "ON":
            return  0x90
        elif self.kind == "OFF":
            return 0x80 + self.channel
        elif self.kind == "CC":
            return 0xB0 + self.channel
        elif self.kind == "CCR":
            return 0xB0 + self.channel
        elif self.kind == "PC":
            return 0xC0 + self.channel
        else:
            return 0xFF

def to_tuple(data):
    """Recursively converts a nested list to a nested tuple."""
    if isinstance(data, list):
        # Recursively apply to items and wrap in a tuple
        return tuple(to_tuple(item) for item in data)
    else:
        # Base case: item is not a list (int, string, etc.)
        return data

        
# 3 dimensional list for a bank
# Four Banks ((0-4), 
# Eight buttons + Volume Pedal (0-8)
# Two states on=0, off=1
bank_pedal_onoff = [
    # bank number 0
    [[midipedal("ON",0x00,0xFF,0x7F,0x01,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x01,0x00)],
     [midipedal("ON",0x01,0xFF,0x7F,0x01,0x00),
      midipedal("OFF",0x01,0xFF,0x00,0x01,0x00)],
     [midipedal("ON",0x02,0xFF,0x7F,0x01,0x00),
      midipedal("OFF",0x02,0xFF,0x00,0x01,0x00)],
     [midipedal("ON",0x03,0xFF,0x7F,0x01,0x00),
      midipedal("OFF",0x03,0xFF,0x00,0x01,0x00)],
     [midipedal("ON",0x04,0xFF,0x7F,0x01,0x00),
      midipedal("OFF",0x04,0xFF,0x00,0x01,0x00)],
     [midipedal("ON",0x05,0xFF,0x7F,0x01,0x01),
      midipedal("OFF",0x05,0xFF,0x00,0x01,0x01)],
     [midipedal("ON",0x06,0xFF,0x7F,0x01,0x02),
      midipedal("OFF",0x06,0xFF,0x00,0x01,0x02)],
     [midipedal("ON",0x07,0xFF,0x7F,0x01,0x03),
      midipedal("OFF",0x07,0xFF,0x00,0x01,0x03)],
     [midipedal("CCR",0x07,0x7F,0x00,0x01,0x00),
      midipedal("CCR",0x07,0x7F,0x00,0x01,0x00)]
    ],

    # bank number 1
    [[midipedal("ON",0x00,0xFF,0x7F,0x02,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x02,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x02,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x02,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x02,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x02,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x02,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x02,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x02,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x02,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x02,0x01),
      midipedal("OFF",0x00,0xFF,0x00,0x02,0x01)],
     [midipedal("ON",0x00,0xFF,0x7F,0x02,0x02),
      midipedal("OFF",0x00,0xFF,0x00,0x02,0x02)],
     [midipedal("ON",0x00,0xFF,0x7F,0x02,0x03),
      midipedal("OFF",0x00,0xFF,0x00,0x02,0x03)],
     [midipedal("CCR",0x07,0x7F,0x00,0x02,0x00),
      midipedal("CCR",0x07,0x7F,0x00,0x02,0x00)]
    ],

    # bank number 2
    [[midipedal("ON",0x00,0xFF,0x7F,0x03,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x03,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x03,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x03,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x03,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x03,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x03,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x03,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x03,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x03,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x03,0x01),
      midipedal("OFF",0x00,0xFF,0x00,0x03,0x01)],
     [midipedal("ON",0x00,0xFF,0x7F,0x03,0x02),
      midipedal("OFF",0x00,0xFF,0x00,0x03,0x02)],
     [midipedal("ON",0x00,0xFF,0x7F,0x03,0x03),
      midipedal("OFF",0x00,0xFF,0x00,0x03,0x03)],
     [midipedal("CCR",0x07,0x7F,0x00,0x03,0x00),
      midipedal("CCR",0x07,0x7F,0x00,0x03,0x00)]
    ],

    # bank number 3
    [[midipedal("ON",0x00,0xFF,0x7F,0x04,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x04,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x04,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x04,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x04,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x04,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x04,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x04,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x04,0x00),
      midipedal("OFF",0x00,0xFF,0x00,0x04,0x00)],
     [midipedal("ON",0x00,0xFF,0x7F,0x04,0x01),
      midipedal("OFF",0x00,0xFF,0x00,0x04,0x01)],
     [midipedal("ON",0x00,0xFF,0x7F,0x04,0x02),
      midipedal("OFF",0x00,0xFF,0x00,0x04,0x02)],
     [midipedal("ON",0x00,0xFF,0x7F,0x04,0x03),
      midipedal("OFF",0x00,0xFF,0x00,0x04,0x03)],
     [midipedal("CCR",0x07,0x7F,0x00,0x04,0x00),
      midipedal("CCR",0x07,0x7F,0x00,0x04,0x00)]
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

print(loaded_json[0][0][0]["kind"])
print(loaded_json[0][0][0]["val"])
print(loaded_json[0][0][0]["tog"])
print(loaded_json[0][0][0]["vel"])
print(loaded_json[0][0][0]["ch"])
print(loaded_json[0][0][0]["bank"])

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
TOG = 2
VEL = 3
CH = 4
BANK = 5

m_bank = 0
m_pedal = 0
m_onoff = DOWN

a_onoff = loaded_tuple[m_bank][m_pedal][m_onoff]

print(loaded_tuple)

print("# OF BANKS:",len(loaded_tuple))
print("KIND:", a_onoff[KIND]) #kind
print("VAL:", a_onoff[VAL]) #val
print("TOG:", a_onoff[TOG]) #tog
print("VEL:", a_onoff[VEL]) #vel
print("CH:", a_onoff[CH]) #ch
print("BANK:", a_onoff[BANK]) #bank

print("STATUSBYTE:",statusbyte(loaded_tuple[m_bank][m_pedal][m_onoff]))

#list of pedals
def make_pedal_objects(banks,bank):
    build = []
    for i in banks[bank]:
        i0 = i[0]
        i1 = i[1]
        onoff = (midipedal(i0[KIND],i0[VAL],i0[TOG],i0[VEL],i0[CH],i0[BANK]),
                 midipedal(i1[KIND],i1[VAL],i1[TOG],i1[VEL],i1[CH],i1[BANK])                  )
        build.append(onoff)
    return build

def assign_pedal_objects_bank(pedalonoff,banks,bank):
    for i, p in zip(banks[bank], pedalonoff):
        i0 = i[0]
        i1 = i[1]
        p[0].assign(i0[KIND],i0[VAL],i0[TOG],i0[VEL],i0[CH],i0[BANK])
        p[1].assign(i1[KIND],i1[VAL],i1[TOG],i1[VEL],i1[CH],i1[BANK])

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
