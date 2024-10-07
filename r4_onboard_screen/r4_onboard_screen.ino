// To use ArduinoGraphics APIs, please include BEFORE Arduino_LED_Matrix

#include "ArduinoGraphics.h"

#include "Arduino_LED_Matrix.h"


ArduinoLEDMatrix matrix;


void setup() {

  Serial.begin(115200);

  matrix.begin();


 

}

void ON(){
  matrix.beginDraw();
  matrix.stroke(0xFFFFFFFF);
  const char text[] = "ON";
  matrix.textFont(Font_4x6);
  matrix.beginText(0, 1, 0xFFFFFF);
  matrix.println(text);
  matrix.endText();
  matrix.endDraw();

}

void OFF(){
  matrix.beginDraw();
  matrix.stroke(0xFFFFFFFF);
  const char text[] = "OFF";
  matrix.textFont(Font_4x6);
  matrix.beginText(0, 1, 0xFFFFFF);
  matrix.println(text);
  matrix.endText();
  matrix.endDraw();

}
void loop() {


  // Make it scroll!

 ON();

 delay(2000);

 OFF();
 delay(2000);
}