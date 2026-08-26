#include <Adafruit_NeoPixel.h> 
#include <ADCTouch.h>

/*
 WS2811/Neopixel pattern switcher for ATtiny85 (and Arduino)
 Requires Adafruit NeoPixel And ADCTouch
 WS2811 Signal, Digital Pin 0 (PB0)
 Capacitive Touch. ADC channel 1 (PB2)
 GPL v3
 */

// Define
#define NUM_LEDS 4
#define DATA_PIN 0
#define A_TOUCH_PIN 1     // ADC1 is also PB2
#define TOUCH_DELAY 500
#define TOUCH_THRESH 40   // delta above baseline; adjust for pad size
#define NUM_PATTERNS 5
#define CTR_THRESH 16

// Init Vars
uint8_t j = 0;
uint8_t pattern=1;
uint8_t lastPix=0; 
uint8_t myPix=0;
uint8_t direction=1;
uint8_t counter=0;
uint8_t colors[3];
unsigned long mark;
int baseline = 0;

// Per-pattern animation state. Each pattern renders exactly one frame per
// loop() call, so progress has to live here instead of in local loop vars.
uint32_t scanColors[3];   // scanner: the three sweep colours
uint8_t  scanColor = 0;   // scanner: index into scanColors
uint8_t  scanPos   = 0;   // scanner: current pixel position
bool     scanFwd   = true;// scanner: sweep direction
uint8_t  wipePos   = 0;   // colorWipe: next pixel to fill
uint32_t wipeColor = 0;   // colorWipe: colour of the current pass
float    waveIn    = 0.0; // wavey: sine phase

// Start Strip
Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, DATA_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
    // Set ADC prescaler to 64 for a stable 125kHz clock at 8MHz
    ADCSRA |= (1 << ADPS2) | (1 << ADPS1);
    ADCSRA &= ~(1 << ADPS0);

    // Calibrate baseline over 100 readings
    long sum = 0;
    for (int i = 0; i < 100; i++) {
        sum += ADCTouch.read(A_TOUCH_PIN, 10);
        delay(5);
    }
    baseline = sum / 100;

    strip.begin();
    strip.show(); // Initialize all pixels to 'off'

    // One-time colour setup for the frame-based patterns
    scanColors[0] = strip.Color(255, 0, 0);
    scanColors[1] = strip.Color(200, 0, 100);
    scanColors[2] = strip.Color(64, 0, 200);
    wipeColor = strip.Color(random(255), random(255), random(255));
}

/*
 * Touch handling:
 * chkTouch() is called exactly once per loop() iteration.
 *
 * Originally the multi-frame patterns (scanner, colorWipe, wavey) were
 * blocking: each ran its whole animation pass in an internal for-loop with
 * delays before returning to loop(). A touch could only be noticed mid-pass
 * if chkTouch() was also called inside those inner loops, so every animated
 * frame re-polled the sensor and could break out early.
 *
 * The patterns are now one-frame-per-call state machines (scannerFrame,
 * colorWipeFrame, waveyFrame), so loop() regains control between every frame
 * and this single poll is enough. A touch resets the pattern's animation
 * state via resetPatternState(), so the new pattern starts from the
 * beginning - the same responsiveness the inner breaks gave before.
 *
 * Patterns only set pixels and return their frame delay; loop() does the
 * one strip.show() and delay() for every pattern.
 */
void loop() {
    // if touched, advance pattern and restart its animation
    if (chkTouch(ADCTouch.read(A_TOUCH_PIN, 10))) {
        resetPatternState();
    }

    // if pattern greater than #pattern reset
    if (pattern > NUM_PATTERNS) { pattern = 1; }

    // render one frame of the current pattern, flush the strip,
    // then wait the frame delay chosen by the pattern
    uint8_t frameDelay = pickPattern(pattern);
    strip.show();
    delay(frameDelay);

    // set direction
    if (direction == 1) { j++;  } else {  j--; }

    if (j > 254) { direction = 0; }
    if (j < 1) { direction = 1; }   
	
}

/* render one frame of the selected pattern; returns the ms to wait
   before the next frame */
uint8_t pickPattern(uint8_t var) {
      switch (var) {
        case 1:
          // scanner, bounces one pixel end to end through 3 colours
          return scannerFrame();
        case 2:
          // color wipe random RGB, new colour each pass
          return colorWipeFrame();
        case 3:
          // color wave - hue oscillates between 200 and 240
          return waveyFrame();
        case 4:
          // rainbow firefly, 1px at random
          counter++;
          return colorFirefly(60);
        case 5:
          // rainbow solid
          counter++;
          return rainbow(10);
      }
      return 0;
}

/* restart the current pattern's animation from the beginning */
void resetPatternState() {
    scanColor = 0;
    scanPos   = 0;
    scanFwd   = true;
    wipePos   = 0;
    wipeColor = strip.Color(random(255), random(255), random(255));
    waveIn    = 0.0;
    counter   = 0;
    myPix     = 0;
    lastPix   = 0;
}

/* check button state */
boolean chkTouch(int touchVal) {
   int touchDelta = touchVal - baseline;
   if (touchDelta > TOUCH_THRESH && (millis() - mark) > TOUCH_DELAY) {
       j = 0;
       mark = millis();
       pattern++;
       return true;
    } 
    else { return false; }
}

uint8_t colorFirefly(int wait) {
        if(myPix != lastPix) {
          if(counter<CTR_THRESH) {
            float colorV = sin((6.28/30)*(float)(counter)) *255;
            HSVtoRGB((359/CTR_THRESH)*counter, 255, colorV, colors);
            strip.setPixelColor(myPix, colors[0], colors[1], colors[2]);
            return wait;
          } else {
            lastPix=myPix;
            counter=0;
            colorFast(0);
          }
        } else {
          myPix=random(0,strip.numPixels());
        }
        return 0;
	
}

// Fill the dots one after the other with a color - one frame per call.
// When the fill completes a new random colour is picked for the next pass.
uint8_t colorWipeFrame() {
  strip.setPixelColor(wipePos, wipeColor);

  if (++wipePos >= NUM_LEDS) {
      wipePos = 0;
      wipeColor = strip.Color(random(255), random(255), random(255));
  }
  return 50;
}

// fill every pixel with a colour (loop() flushes the strip)
void colorFast(uint32_t c) {
    for (uint16_t i = 0; i < strip.numPixels(); i++) {
        strip.setPixelColor(i, c);
    }
}

uint8_t rainbow(uint8_t wait) {
    uint16_t i;

    for (i = 0; i < strip.numPixels(); i++) {
        strip.setPixelColor(i, Wheel((i + j) & 255));
    }
    return wait;
}

// scanner - one frame per call.
// A single pixel bounces end to end; when it returns to the start the
// colour advances through scanColors[3].
uint8_t scannerFrame() {
    colorFast(0);
    strip.setPixelColor(scanPos, scanColors[scanColor]);

    if (scanFwd) {
        if (scanPos >= NUM_LEDS - 1) {
            scanFwd = false;
        } else {
            scanPos++;
        }
    } else {
        if (scanPos == 0) {
            scanColor = (scanColor + 1) % 3;
            scanFwd = true;
        } else {
            scanPos--;
        }
    }
    return 50;
}

// sine wave - one frame per call. Hue oscillates between 200 and 240 with
// a phase offset per pixel; the phase advances 0.06 rad per frame.
uint8_t waveyFrame() {
    int diff = 240 - 200;
    for (int i = 0; i < NUM_LEDS; i++) {
        float out = sin(waveIn + i * (6.283 / NUM_LEDS)) * diff + 200;
        HSVtoRGB(out, 255, 255, colors);
        strip.setPixelColor(i, colors[0], colors[1], colors[2]);
    }

    waveIn += 0.06;
    if (waveIn >= 6.283) { waveIn = 0; }
    return 0; // run as fast as possible
}

// helpers 

uint32_t Wheel(byte WheelPos) {
    if (WheelPos < 85) {
        return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
    } else if (WheelPos < 170) {
        WheelPos -= 85;
        return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
    } else {
        WheelPos -= 170;
        return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
    }
}


// HSV to RGB colors
// hue: 0-359, sat: 0-255, val (lightness): 0-255
// adapted from http://funkboxing.com/wordpress/?p=1366
void HSVtoRGB(int hue, int sat, int val, uint8_t * colors) {
    int base;
    if (sat == 0) { // Achromatic color (gray).
        colors[0] = val;
        colors[1] = val;
        colors[2] = val;
    } else {
        base = ((255 - sat) * val) >> 8;
        switch (hue / 60) {
        case 0:
            colors[0] = val;
            colors[1] = (((val - base) * hue) / 60) + base;
            colors[2] = base;
            break;
        case 1:
            colors[0] = (((val - base) * (60 - (hue % 60))) / 60) + base;
            colors[1] = val;
            colors[2] = base;
            break;
        case 2:
            colors[0] = base;
            colors[1] = val;
            colors[2] = (((val - base) * (hue % 60)) / 60) + base;
            break;
        case 3:
            colors[0] = base;
            colors[1] = (((val - base) * (60 - (hue % 60))) / 60) + base;
            colors[2] = val;
            break;
        case 4:
            colors[0] = (((val - base) * (hue % 60)) / 60) + base;
            colors[1] = base;
            colors[2] = val;
            break;
        case 5:
            colors[0] = val;
            colors[1] = base;
            colors[2] = (((val - base) * (60 - (hue % 60))) / 60) + base;
            break;
        }

    }
}
