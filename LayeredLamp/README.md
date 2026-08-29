# LayeredLamp

A 3D-printable table lamp built from **stacked, randomly-offset cube layers**, with a small **ATtiny85 + NeoPixel** controller driven by a **capacitive touch pad**. Each touch of the pad cycles through five lighting patterns.

The lamp body is generated parametrically in OpenSCAD (`StackedCubeLayers.scad`), printed in clear material, and stacked on octagonal pins that pass through a vertical wire slot running the full height of the body.

---

## Directory Layout

| Path | Type | Description |
| --- | --- | --- |
| `StackedCubeLayers.scad` | OpenSCAD | Main parametric model — generates lamp body, stacking pin, or base (`type = "lamp" \| "pin" \| "bottom"`) |
| `StackedCubes.scad` | OpenSCAD | Early 4-layer prototype/test that the main model is based on |
| `StackedCubeLayers.json` | JSON | Saved OpenSCAD parameter set (layers=40, z=4, random_range≈0.41) from a parameter-editor plugin |
| `Lamp_1.stl` … `Lamp_4.stl` | STL (ASCII) | Exported lamp bodies, one per random seed |
| `Bottom.stl` | STL (ASCII) | Base plate with pocket and top pin |
| `pin_8.stl` | STL (ASCII) | Octagonal stacking pin (standalone export) |
| `LampClear.3mf`, `LampClear_2.3mf` | 3MF | Sliced print files for the clear lamp body (Slic3r PE / QIDI, incl. wipe-tower metadata) |
| `LedCodeAttiny85_ADCTouch/LedCodeAttiny85_ADCTouch.ino` | Arduino | Firmware v2 — touch via **ADCTouch** library on PB2 (current) |
| `LedCodeAttinyTouch85/LedCodeAttinyTouch85.ino` | Arduino | Firmware v1 — alternate pattern set (scanner/wipe/wavey/firefly/rainbow), touch via **ADCTouch** (GPL v3) |
| `LedAttinyTouchx2/LedAttinyTouchx2.ino` | Arduino | Firmware v3 — 30-px strip, dual touch pads (color + pattern), EEPROM persistence of settings, 8 patterns |
| `ATtiny85 NeoPixel + Capacitive Touch.md` | Markdown | Full build guide: BOM, wiring, libraries, sketch, flashing, tuning, troubleshooting |
| `ATTINY85_Pinout.png` | Image | ATtiny85 pinout reference |

---

## CAD Model (`StackedCubeLayers.scad`)

Requires the **BOSL2** library. The body is a `polyhedron` built from stacked square "layers"; each intermediate layer's four corners are independently scaled by a seeded random factor, giving an organic, slightly twisted stack. A `minkowski()` with a 0.5 mm sphere rounds the edges before cuts.

### Key parameters (defaults in file)

| Parameter | Default | Meaning |
| --- | --- | --- |
| `layers` | 27 | Number of stacked layers |
| `x`, `y` | 50, 50 | Base footprint per layer (mm) |
| `z` | 6 | Layer thickness (mm); total height ≈ `(layers-1)·z` + pin |
| `random_range` | 0.25 | Corner offset magnitude (± fraction of layer size) |
| `slot_w`, `slot_d` | 11, 3.5 | Vertical wire slot width/depth (mm), cut full height through one side face |
| `bottom_size` | [120, 120, 40] | Base plate outer size |
| `bottom_inside` | [95, 95, 25] | Base pocket (holds electronics) |
| `type` | `"lamp"` | What to render: `lamp`, `pin`, or `bottom` |

### Output variants

- **`type = "lamp"`** — body with the wire slot and a ×2-scaled octagonal pin cut out of the bottom; a matching pin is added on top (shown in red for preview). The top/bottom corner rings are kept square so layers stack flush.
- **`type = "pin"`** — the standalone octagonal stacking pin (`pin_8()`: two 8-sided prisms joined with `hull()`, rotated 90°/22.5°).
- **`type = "bottom"`** — chamfered base plate with a recessed pocket and top pin.

### Random seeds (reproducible exports)

| Seed | Export |
| --- | --- |
| `123458` | `Lamp_1.stl` |
| `123461` | `Lamp_2.stl` |
| `123471` | `Lamp_3.stl` |
| `123476` (active) | `Lamp_4.stl` |

### Exported STL dimensions (measured bounding boxes)

| File | Triangles | X × Y (mm) | Z height (mm) |
| --- | ---: | --- | ---: |
| `Lamp_1.stl` | 1,936 | ~62.8 × 62.9 | 156.9 |
| `Lamp_2.stl` | 1,980 | ~63.2 × 63.2 | 156.9 |
| `Lamp_3.stl` | 2,044 | ~63.0 × 63.0 | 169.4 |
| `Lamp_4.stl` | 2,080 | ~63.0 × 62.8 | 169.4 |
| `Bottom.stl` | 108 | 120.0 × 120.0 | 40.0 |
| `pin_8.stl` | 60 | ~9.7 octagon, 26.0 long | — |

> The footprint is larger than the nominal 50 mm because corner offsets can scale layers up to `1 + random_range`.

### Sliced files

`LampClear.3mf` / `LampClear_2.3mf` are ready-to-print 3MFs of the clear lamp body, sliced with **Slic3r PE (QIDI)**. The second file is a later re-slice (Aug 21 vs Aug 18).

---

## Electronics

### Hardware

- **MCU:** ATtiny85 (8 KB flash / 512 B SRAM), 1 MHz internal or 16 MHz external clock
- **LEDs:** WS2812B NeoPixel strip — 4 pixels in the current firmware (design doc targets up to 8–16)
- **Touch:** bare wire / copper-tape pad, no dedicated IC

### Pin map

| ATtiny85 pin | Function | Notes |
| --- | --- | --- |
| PB0 (pin 1) | NeoPixel DIN | via 470 Ω series resistor |
| PB2 (A1/ADC1) | Capacitive touch pad | used by firmware v2 (`ADCTouch`) |
| — | VCC / GND | strip powered from separate 5 V supply; **shared GND required** |

### Firmware

Both sketches live in their own Arduino-IDE-style folders and implement the same five patterns, advanced one step per touch:

| # | Pattern | Behaviour |
| --- | --- | --- |
| 0/1 | Solid / Scanner | Single colour (hue drifts) or a pixel scanning back and forth |
| 1/2 | Rainbow / Wipe | Full-spectrum gradient, or random-colour wipe |
| 2/3 | Breathe / Wave | Triangle-wave brightness fade, or sine hue wave |
| 3/4 | Chase / Firefly | Two bright pixels running the strip, or one pixel flickering at random positions |
| 4/5 | Twinkle / Rainbow solid | Per-pixel pseudo-random colours/brightness, or full-strip rainbow cycle |

- **`LedCodeAttiny85_ADCTouch.ino`** (current) — uses `Adafruit_NeoPixel` + **ADCTouch**. Calibrates a baseline from 100 ADC samples at startup; triggers when the reading exceeds baseline by `THRESHOLD = 40`. Pattern frames are only recomputed every 90th loop so touch sampling stays responsive. Integer-only HSV→RGB (no floats).
- **`LedCodeAttinyTouch85.ino`** (earlier pattern set, GPL v3) — also uses `Adafruit_NeoPixel` + **ADCTouch** on ADC1 (PB2), with baseline calibration and a 500 ms touch debounce. All five patterns are one-frame-per-call state machines (progress kept in per-pattern variables): each only sets pixels and returns its frame delay, and `loop()` does the single `strip.show()` + `delay()` for every pattern. `loop()` also polls the touch sensor exactly once per frame; a touch calls `resetPatternState()` to restart the new pattern from the beginning, giving the same immediate-interrupt feel as the original design (which had to re-poll the sensor inside each blocking animation loop).

### Building / flashing with arduino-cli

Both sketches target an **ATtiny85 at 8 MHz**:

```
arduino-cli compile --fqbn attiny:avr:ATtinyX5:cpu=attiny85,clock=internal8 <sketch-folder>
```

Use `clock=external8` if the board has an external 8 MHz crystal. Gotchas: multiple
FQBN options are **comma**-separated (colon-separated fails with "Invalid FQBN");
omitting `cpu=attiny85` silently builds for the ATtiny25 (2 KB flash) and overflows;
the default 1 MHz clock breaks Adafruit_NeoPixel (`#error CPU SPEED NOT SUPPORTED`).
Current `LedAttinyTouchx2` size: 7214 / 8192 B flash (88 %), 139 / 512 B SRAM (27 %).

### Build guide

See **`ATtiny85 NeoPixel + Capacitive Touch.md`** for the complete reference: bill of materials, wiring diagram, library installation, the original RC charge-time touch sketch, Arduino IDE and `avrdude` flashing instructions (incl. 1 MHz internal-clock fuses), power budget (5 V / 3 A supply recommended, 100 µF bulk cap across the strip), tuning table, and troubleshooting.

> Note: that document describes the original design (8 pixels, RC touch on PB1). The shipped firmware evolved to 4 pixels with ADCTouch-based sensing on PB2 — see the pin map above for the current wiring.

---

## Assembly

1. Print `Bottom.stl` (base) and one of the `Lamp_*.stl` bodies in clear material (or use the pre-sliced `.3mf` files).
2. Flash an ATtiny85 with the ADCTouch sketch; wire PB0 → 470 Ω → NeoPixel DIN, touch pad to PB2, shared GND.
3. Mount the electronics and strip in the base pocket (95 × 95 × 25 mm).
4. Stack the lamp body on the base pin; run the data wire up through the full-height slot (11 × 3.5 mm) so it exits at the top.
