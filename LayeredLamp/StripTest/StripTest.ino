#include <Adafruit_NeoPixel.h>

#define LED_PIN    0      // ATtiny85 Pin PB0 (Digital Pin 0)
#define NUM_LEDS   4     // Change this to match your strip length

// Setup NeoPixel strip object
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  strip.begin();           // Initialize pixel object
  strip.show();            // Turn off all pixels safely
  strip.setBrightness(50); // Set brightness (0 to 255)
}

void loop() {
  colorWipe(strip.Color(255, 0, 0), 50); // Red
  colorWipe(strip.Color(0, 255, 0), 50); // Green
  colorWipe(strip.Color(0, 0, 255), 50); // Blue
}

// Fill strip pixels one after another with a color
void colorWipe(uint32_t color, int wait) { // wait compatibility note: standard uint32_t
  for(int i=0; i<strip.numPixels(); i++) {
    strip.setPixelColor(i, color);
    strip.show();
    delay(wait);
  }
}
