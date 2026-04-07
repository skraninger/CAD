import sys
import time

# --- HARDWARE & EMULATION SELECTION ---
try:
    if sys.platform == "microcontroller":
        import board
        import usb_midi
        import keypad
        import neopixel
        import analogio
        IS_DESKTOP = False
    else:
        raise ImportError
except (ImportError, AttributeError):
    import tkinter as tk
    from tkinter import ttk
    IS_DESKTOP = True

# --- EMULATION CLASSES ---
if IS_DESKTOP:
    class MockEvent:
        def __init__(self, key_number, pressed):
            self.key_number = key_number
            self.pressed = pressed
            self.released = not pressed

    class VirtualHardware:
        def __init__(self):
            self.events_queue = []
            self.pot_value = 0
        def get_event(self):
            return self.events_queue.pop(0) if self.events_queue else None

    vh = VirtualHardware()

# --- INITIALIZATION ---
CHANNEL = 0
VOL_CC_NUMBER = 7
midi_notes = [60, 61, 62, 63, 64, 65, 66, 67] # Outgoing notes for 8 physical buttons
last_midi_volume = -1
INITIAL_COLOR = (255, 255, 255) # White

# New state tracking for Toggle mode
button_states = [False] * 8  # Track if a note is currently "ON"
toggle_modes = [None] * 8    # Will hold references to the UI checkbox variables

if not IS_DESKTOP:
    midi_in = usb_midi.ports[0]
    midi_out = usb_midi.ports[1]
    pixels = neopixel.NeoPixel(board.NEOPIXEL, 8, brightness=0.5, auto_write=True)
    pixels.fill(INITIAL_COLOR)
    potentiometer = analogio.AnalogIn(board.A0)
    button_pins = (board.GP0, board.GP1, board.GP2, board.GP3,
                   board.GP4, board.GP5, board.GP6, board.GP7)
    keys = keypad.Keys(button_pins, value_when_pressed=False, pull=True)

    
# --- CORE LOGIC ---
def handle_incoming_midi(status, note_num, velocity):
    """Processes incoming MIDI notes and updates NeoPixel colors/octaves."""

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

def update_midi_logic_2():
    global last_midi_volume
    
    event = vh.get_event() if IS_DESKTOP else keys.events.get()

    if event:
        idx = event.key_number
        note = midi_notes[idx]
        
        # Check if "Toggle Mode" is active for this specific button
        is_toggle = toggle_modes[idx].get() if IS_DESKTOP else False # Add hardware toggle logic here if needed

        if is_toggle:
            # TOGGLE LOGIC: Only trigger on Press
            if event.pressed:
                button_states[idx] = not button_states[idx] # Flip state
                if button_states[idx]:
                    send_raw_midi(0x90 + CHANNEL, note, 120)
                    set_pixel_color(idx, (0, 255, 100)) # Green
                else:
                    send_raw_midi(0x80 + CHANNEL, note, 0)
                    set_pixel_color(idx, INITIAL_COLOR)
        else:
            # MOMENTARY LOGIC: Standard behavior
            if event.pressed:
                send_raw_midi(0x90 + CHANNEL, note, 120)
                set_pixel_color(idx, (0, 255, 100))
            if event.released:
                send_raw_midi(0x80 + CHANNEL, note, 0)
                set_pixel_color(idx, INITIAL_COLOR)

    # Volume Logic remains the same...
    raw_val = vh.pot_value if IS_DESKTOP else potentiometer.value
    current_midi_volume = raw_val // 516

    if current_midi_volume != last_midi_volume:
        send_raw_midi(0xB0 + CHANNEL, VOL_CC_NUMBER, current_midi_volume)
        last_midi_volume = current_midi_volume

# --- HELPER FUNCTIONS ---
def send_raw_midi(status, data1, data2):
    if IS_DESKTOP: print(f"DEBUG MIDI OUT: {[hex(status), data1, data2]}")
    else: midi_out.write(bytearray([status, data1, data2]))

def set_pixel_color(index, color):
    if IS_DESKTOP:
        hex_color = "#%02x%02x%02x" % color
        ui_leds[index].config(bg=hex_color)
    else:
        pixels[index] = color

# --- DESKTOP UI EXECUTION ---
if IS_DESKTOP:
    root = tk.Tk()
    root.title("MIDI Controller Simulator")
    ui_leds = []
    
    # 1. Virtual NeoPixels (Same as before)
    led_frame = ttk.LabelFrame(root, text=" NeoPixels ", padding=10)
    led_frame.pack(pady=5)
    for i in range(8):
        led = tk.Canvas(led_frame, width=20, height=20, bg="#ffffff", highlightthickness=1)
        led.grid(row=0, column=i, padx=10)
        ui_leds.append(led)

    # 2. Toggle Mode Checkboxes (NEW)
    toggle_frame = ttk.LabelFrame(root, text=" Enable Toggle Mode (Per Button) ", padding=10)
    toggle_frame.pack(pady=5)
    for i in range(8):
        var = tk.BooleanVar(value=False)
        toggle_modes[i] = var
        chk = tk.Checkbutton(toggle_frame, text=f"Tgl {i}", variable=var)
        chk.grid(row=0, column=i, padx=5)

    # 3. Outgoing MIDI Buttons
    hw_frame = ttk.LabelFrame(root, text=" Physical Controller Buttons ", padding=10)
    hw_frame.pack(pady=5)
    for i in range(8):
        btn = tk.Button(hw_frame, text=f"Btn {i}", width=6)
        btn.bind("<ButtonPress-1>", lambda e, x=i: vh.events_queue.append(MockEvent(x, True)))
        btn.bind("<ButtonRelease-1>", lambda e, x=i: vh.events_queue.append(MockEvent(x, False)))
        btn.grid(row=0, column=i, padx=2)

    # 3. Incoming MIDI Simulator (3 Octaves of 1st 8 chromatic notes)
    sim_frame = ttk.LabelFrame(root, text=" MIDI Input Simulator (Notes 60-95) ", padding=10)
    sim_frame.pack(pady=10)
    
    # Chromatic notes (C, C#, D, D#, E, F, F#) across 3 octaves
    naturals = [0, 1, 2, 3, 4, 5, 6]
    octaves = [60, 72, 84]
    
    for octave_idx, base_note in enumerate(octaves):
        for note_idx, offset in enumerate(naturals):
            note = base_note + offset
            btn = tk.Button(sim_frame, text=str(note), width=3, height=2, bg="white")
            btn.bind("<ButtonPress-1>", lambda e, n=note: handle_incoming_midi(0x90, n, 100))
            btn.bind("<ButtonRelease-1>", lambda e, n=note: handle_incoming_midi(0x80, n, 0))
            btn.grid(row=0, column=(octave_idx * 7) + note_idx, padx=1)

    # 4. Volume Scale
    scale = ttk.Scale(root, from_=0, to=65535, orient="horizontal", command=lambda v: setattr(vh, 'pot_value', int(float(v))))
    scale.pack(fill="x", padx=20, pady=10)

    def loop():
        update_midi_logic_2()
        root.after(10, loop)
    
    loop()
    root.mainloop()
else:
    while True:
        update_midi_logic_2()