
#include "OneWire.h"
#include "DallasTemperature.h"




int isRunning = 0;
float tempInput; // Temperature we want
float tempInsideOutput; // Temperature we have inside
float tempOutsideOutput; // Temperature we have outside
float phInput; // pH we want


float phNapiecieElektryczneBoMichalSieZesra;



float phValueOutput; // pH we have
float o2ValueOutput;
int oxygenInput;
int oxygenOutput;
int stirRPM;
int antifoamInput;
int antifoamOutput;
int airRpmInput;
int sampleSignal = 0;
int stopSignal = 0;
unsigned long int cycleStartTime;
unsigned long int cycleEndTime;
String commentOutput;


unsigned long int totalCycleTime = 0;



// define pins
 
#define free0 0
#define free1 1

#define airPump 2
#define pwmAirPump 3

#define waterPump 4


#define pwmAntifoam 5
#define antifoam 6

#define pwmProbePump  7
#define probePump 8
#define probePumpSuck 9 



#define pwmAcidPump2 10
#define pwmRulePump1 11
#define pwmStirrer 12 // speed of Stirrer (mieszadlo)
#define free13 13 // freee pwm

#define Stirrer 14
#define acidPump2 15 // peristalticPump 2
#define rulePump1 16 // peristalticPump 1

#define phSensor A1 //ph Sensor 15 pin analog
#define o2Sensor A2 // o2 sensor 16 pin analog




#define tempSensors 52 // both temperature sensors digital 


#define heaterRelay 53 // heater relay digital 

OneWire oneWire(tempSensors);
DallasTemperature tempSensorsOneWire(&oneWire);
//byte tempInsideSensorAdress[8] = {0x28, 0x18, 0x12, 0x43, 0xD4, 0xE1, 0x3C, 0x58}; // ten z kablami 
byte tempOutsideSensorAdress[8] = {0x28, 0x9C, 0xE4, 0x43, 0xD4, 0xE1, 0x3C, 0x54}; // trytytka 
byte tempInsideSensorAdress[8] = {0x28, 0x55, 0xDC, 0x43, 0xD4, 0xE1, 0x3C, 0xE7}; // ten z izolacja

void setup() {
 

  Serial.begin(115200);

  tempSensorsOneWire.begin();
  tempSensorsOneWire.setResolution(12);
  pinMode(airPump, OUTPUT);    
  pinMode(pwmProbePump, OUTPUT);
  pinMode(waterPump, OUTPUT);
  pinMode(pwmAntifoam, OUTPUT);    
  pinMode(pwmAirPump, OUTPUT);
  pinMode(Stirrer, OUTPUT);

  pinMode(probePumpSuck, OUTPUT);

   
  pinMode(pwmAcidPump2, OUTPUT);
  pinMode(pwmRulePump1, OUTPUT);
  pinMode(pwmStirrer, OUTPUT); 
  pinMode(acidPump2, OUTPUT);    
  pinMode(rulePump1, OUTPUT);
  
  //pinMode(tempSensors, INPUT); // instance of onewire class
  
  pinMode(phSensor, INPUT);
  pinMode(o2Sensor, INPUT);
  pinMode(heaterRelay, OUTPUT);
  pinMode(probePump, OUTPUT);
  pinMode(antifoam, OUTPUT);
  


// ======= manual input for debugging 
  sampleSignal = 0;
  commentOutput = "test_comment";
  tempInput = 30.0;
  phInput = 7.0;
  stirRPM = 0; // send in PWM 
  antifoamInput = 0;
  isRunning = 1;
  sampleSignal = 3; // 3 off
  stopSignal = 0;
  airRpmInput = 255;

}


  




void loop() {
  

  phNapiecieElektryczneBoMichalSieZesra = analogRead(phSensor) * 0.0049;

  phValueOutput =  3.4468*phNapiecieElektryczneBoMichalSieZesra + 0.9253;
  Serial.println(phNapiecieElektryczneBoMichalSieZesra);



  //Serial.println(phValueOutput);

  delay(1000);


}


