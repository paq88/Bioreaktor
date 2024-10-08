/* DS18B20 1-Wire digital temperature sensor with Arduino example code. More info: https://www.makerguides.com */
// https://www.makerguides.com/ds18b20-arduino-tutorial/

// Include the required Arduino libraries:
#include "OneWire.h"
#include "DallasTemperature.h"


// Define to which pin of the Arduino the 1-Wire bus is connected:
#define ONE_WIRE_BUS 2

// Create a new instance of the oneWire class to communicate with any OneWire device:
OneWire oneWire(ONE_WIRE_BUS);

// Pass the oneWire reference to DallasTemperature library:
DallasTemperature sensors(&oneWire);

void setup() {
  // put your setup code here, to run once:

Serial.begin(9600);
sensors.begin();


}

void loop() {
  // put your main code here, to run repeatedly:


  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);

  Serial.print("temp C:");
  //Serial.print(millis());
  Serial.print(" ");
  Serial.println(tempC);

  delay(3000);

}
