/* DS18B20 1-Wire digital temperature sensor with Arduino example code. More info: https://www.makerguides.com */
// https://www.makerguides.com/ds18b20-arduino-tutorial/

// Include the required Arduino libraries:
#include "OneWire.h"
#include "DallasTemperature.h"


// Define to which pin of the Arduino the 1-Wire bus is connected:
#define ONE_WIRE_BUS 22

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
  float tempC1 = sensors.getTempCByIndex(0);
  float tempC2 = sensors.getTempCByIndex(1);
  float tempC3 = sensors.getTempCByIndex(2);



  Serial.print("temp C:");
  //Serial.print(millis());
  Serial.print(" ");
  Serial.print(tempC1);
  Serial.print(" ");
  Serial.print(tempC2);
  Serial.print(" ");
  Serial.println(tempC3);
  delay(3000);

}
