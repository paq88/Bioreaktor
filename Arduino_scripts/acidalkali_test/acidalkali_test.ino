
#include "OneWire.h"
#include "DallasTemperature.h"




int isRunning = 0;
float tempInput; // Temperature we want
float tempInsideOutput; // Temperature we have inside
float tempOutsideOutput; // Temperature we have outside
int phInputSignal; // signal to add alkali/acid  --- 0 - nothing, 1-add drop of acid 2- add drop of alkali 
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



void setup() {
 

  Serial.begin(115200);


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
  phInputSignal = 0; 
  stirRPM = 0; // send in PWM 
  antifoamInput = 0;
  isRunning = 1;
  sampleSignal = 3; // 3 off
  stopSignal = 0;
  airRpmInput = 0;

}


  




void loop() {
 
  
  
  
  
  //=========================================== INPUT READ ==================================================
  if (Serial.available() > 0) {
    // Read the input from the serial port until a newline character is encountered
    String input = Serial.readStringUntil('\n');
    input.trim(); // Remove any trailing newline characters


    int count = 0;
    // Split the string
    String* input_arr = splitString(input, ',', count);


    // Convert the strings to appropriate types
    tempInput = input_arr[0].toFloat();
    phInputSignal = input_arr[1].toInt(); // ph input is now signal to add one drop of alkali/acid
    stirRPM = input_arr[2].toInt();
    antifoamInput = input_arr[3].toInt();
    airRpmInput = input_arr[4].toInt();
    isRunning = input_arr[5].toInt();
    sampleSignal = input_arr[6].toInt();
    stopSignal = input_arr[7].toInt();


    // Free the allocated memory
    delete[] input_arr;

  }
  


//=======================acid/alkali=============

phInputSignal = 1;



if(phInputSignal == 0){}
else if (phInputSignal == 1){ //drop of acid (around 2.85 seconds to make a drop)

engineStartStop(acidPump2, 255);
delay(2900);
engineStartStop(acidPump2, 0);
delay(3000);


}
else if (phInputSignal == 2 ) { //drop  of alkali 

digitalWrite(acidPump2,HIGH);

}



//====================== SAMPLE ================
//sampleSignal = 0;
    if(sampleSignal == 0){
      }
               
     else if (sampleSignal == 1){
      digitalWrite(probePump, HIGH); //23
      digitalWrite(probePumpSuck, LOW); //8
      analogWrite(pwmProbePump, 255); // 3 
      commentOutput += "Sample taking in progress";
        
      }
     else if(sampleSignal == 2){
      digitalWrite(probePump, LOW);
      digitalWrite(probePumpSuck, HIGH);
      analogWrite(pwmProbePump, 255); 
      commentOutput+="Sample taken returning remains";
      }
     else if (sampleSignal == 3){
      digitalWrite(probePump, LOW);
      digitalWrite(probePumpSuck, LOW);
      analogWrite(pwmProbePump, 0); 
      commentOutput+="Process of sampling ended";
      }
     

}

//============================= Functions ==============================


String* splitString(const String &str, char delimiter, int &count) {
  count = 1; // At least one substring exists
  for (int i = 0; i < str.length(); i++) {
    if (str[i] == delimiter) {
      count++;
    }
  }


  String* result = new String[count];
  int startIndex = 0;
  int resultIndex = 0;


  for (int i = 0; i <= str.length(); i++) {
    if (str[i] == delimiter || i == str.length()) {
      result[resultIndex++] = str.substring(startIndex, i);
      startIndex = i + 1;
    }
  }


  return result;
}


void engineStartStop(byte enginePin, byte PWM){
byte pwmPin;
byte eng = enginePin; 
switch (eng){
    case airPump:
      pwmPin = pwmAirPump;
      break;
    case waterPump:
      //pwmPin = pwmWaterPump; 
      break;
    case Stirrer:
      pwmPin = pwmStirrer; 
      break; 
    case acidPump2:
      pwmPin = pwmAcidPump2; 
      break; 
    case rulePump1:
      pwmPin = pwmRulePump1; 
      break; 
    case antifoam: 
      pwmPin = pwmAntifoam; 
      break;
    
    }
  if(PWM > 0){
    digitalWrite(enginePin, HIGH);
   analogWrite(pwmPin, PWM); }
   else if(PWM == 0){
    digitalWrite(enginePin, LOW);
    analogWrite(pwmPin, PWM); 
    }

     }
