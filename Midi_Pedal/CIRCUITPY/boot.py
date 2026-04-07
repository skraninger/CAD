import supervisor
import usb_midi
supervisor.set_usb_identification(manufacturer="LooperDimension", product="LooperPedal")
usb_midi.set_names(in_jack_name="LD_MidiIn", out_jack_name="LD_MidiOut",
                    streaming_interface_name="LD_MidiStr",
                    audio_control_interface_name="LD_Midi")
