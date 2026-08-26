# Session State — LayeredLamp firmware work

> Read this first when resuming work in this directory. It captures where the
> opencode session left off so context can be restored without the transcript.
> Last updated: 2026-08-26.

## Project (short)

3D-printable table lamp: OpenSCAD stacked-cube body (`StackedCubeLayers.scad`) +
ATtiny85 driving a 4-pixel WS2812B strip, pattern switched by a capacitive touch
pad on PB2. Full docs in `README.md` (created this session). Build guide:
`ATtiny85 NeoPixel + Capacitive Touch.md` (describes the older 8-px/RC-touch design).

## What was done in this session (in order)

1. **Created `README.md`** — directory layout, CAD params/seeds/dimensions,
   electronics pin map, firmware notes, assembly steps.
2. **Ported `LedCodeAttinyTouch85/LedCodeAttinyTouch85.ino` from
   CapacitiveSensor to ADCTouch** (mirroring the reference sketch in
   `LedCodeAttiny85_ADCTouch/`):
   - `#include <ADCTouch.h>`, touch on ADC1 = PB2 (`A_TOUCH_PIN 1`)
   - ADC prescaler /64 (125 kHz at 8 MHz) set in `setup()`
   - Baseline calibrated from 100 samples × 5 ms at startup
   - `chkTouch()` triggers when reading exceeds baseline by `TOUCH_THRESH 40`,
     with 500 ms debounce (`TOUCH_DELAY`)
3. **Documented + refactored the in-pattern `chkTouch` calls.** Original problem:
   `scanner`, `colorWipe`, `wavey` were *blocking* (whole animation pass ran in an
   internal for-loop with delays), so each frame had to re-poll the sensor itself
   to allow mid-animation touch interrupts. Fix: converted all patterns to
   one-frame-per-call state machines; `loop()` polls touch exactly once per frame
   and calls `resetPatternState()` on a touch (restarts new pattern from the
   beginning — same responsiveness as before).
4. **Centralized `strip.show()` + `delay()` in `loop()`.** Each pattern now only
   sets pixels and returns its frame delay; `pickPattern()` returns it and
   `loop()` does the single `strip.show()` + `delay(frameDelay)`. Per-pattern
   pacing preserved: scanner 50 ms, wipe 50 ms, wavey 0 (max speed), firefly
   60 ms, rainbow 10 ms.
5. **Removed dead code:** functions `colorWipeCenter`, `rainbowCycle`,
   `bounceInOut`, `fadeEveOdd`, `twinkleRand`, `waveIntensity`; unused vars
   `buttonState`, `setColor`; unused locals `r,g,b` in `HSVtoRGB`. File went
   407 → ~306 lines. Also fixed stale header comment (data pin listed as 4,
   actually PB0 / `DATA_PIN 0`).

## Current firmware architecture (`LedCodeAttinyTouch85.ino`)

- **Pins:** NeoPixel DIN = PB0 (`DATA_PIN 0`, via 470 Ω), touch pad = PB2 (ADC1).
  `NUM_LEDS 4`.
- **`loop()`** (single source of truth): `chkTouch(ADCTouch.read(...))` → on
  touch `resetPatternState()`; then `frameDelay = pickPattern(pattern)`;
  `strip.show(); delay(frameDelay);`; then the global `j` phase ramp (1..254,
  bouncing via `direction`) used by `rainbow`.
- **Patterns** (`pickPattern`, all one frame per call, return ms to wait):
  | # | Function | Frame delay | Notes |
  | --- | --- | --- | --- |
  | 1 | `scannerFrame()` | 50 | one pixel bounces 0→3→0; colour cycles `scanColors[3]` (red / magenta / violet) per return to start |
  | 2 | `colorWipeFrame()` | 50 | fills one pixel/frame with `wipeColor`; new random RGB when pass completes |
  | 3 | `waveyFrame()` | 0 | sine hue wave 200–240, per-pixel phase offset, `waveIn += 0.06` rad/frame (wraps at 6.283) |
  | 4 | `colorFirefly(60)` | 60 or 0 | one random pixel lit for `CTR_THRESH` (16) frames, then cleared; HSV colour from `counter` |
  | 5 | `rainbow(10)` | 10 | full-strip `Wheel((i + j) & 255)` gradient driven by global `j` |
- **Per-pattern state vars** (top of file): `scanColors[3]`, `scanColor`,
  `scanPos`, `scanFwd`, `wipePos`, `wipeColor`, `waveIn`. All reset by
  `resetPatternState()` on touch (also resets firefly/rainbow state — intentional,
  uniform restart semantics).
- **Helpers:** `colorFast(c)` = pure buffer fill (no show/delay), `Wheel()`,
  `HSVtoRGB()`.
- A comment block above `loop()` documents the touch-handling design history.

## Git state

- Repo root: `D:/Projects/GIT/skraninger/CAD` (LayeredLamp is a subfolder; git
  paths are prefixed `LayeredLamp/`).
- Session work committed as `2f14a9a` "Ported LedCodeAttinyTouch85 to ADCTouch
  with frame-based patterns and added README" (the `.ino` + `README.md`).
- Previous commit `34cf442` "Additional led strip code" still contains the
  ORIGINAL CapacitiveSensor version of the sketch.
- Untracked: `LayeredLamp/SESSION_STATE.md` (this file) — kept out of the
  commit on purpose; add or gitignore it as preferred.

## Next steps / open items

1. **Flash and test on hardware** — no Arduino toolchain (`arduino-cli`) is
   available in this environment, so nothing has been compile-checked. Build for
   ATtiny85 (Adafruit NeoPixel + ADCTouch libraries) and verify all 5 patterns
   and touch switching behave as before.
2. Optional follow-ups (not requested yet):
   - Apply the same frame-based / centralized show-delay treatment to
     `LedCodeAttiny85_ADCTouch/LedCodeAttiny85_ADCTouch.ino` if desired.
   - `ATtiny85 NeoPixel + Capacitive Touch.md` still documents the original
     8-px RC-touch design; could be updated to match current firmware.
