
#include "OneWire.h"
#include "DallasTemperature.h"




int isRunning = 0;
float tempInput; // Temperature we want
float tempInsideOutput; // Temperature we have inside
float tempOutsideOutput; // Temperature we have outside
float phInput; // pH we want
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
#define pwmProbePump  3
#define waterPump 4
#define pwmAntifoam 5
#define pwmAirPump 6
#define Stirrer 7
#define probePumpSuck 8 
#define pwmAcidPump2 9
#define pwmRulePump1 10
#define pwmStirrer 11 // speed of Stirrer (mieszadlo)
#define acidPump2 12 // peristalticPump 2
#define rulePump1 13 // peristalticPump 1

#define phSensor A1 //ph Sensor 15 pin analog
#define o2Sensor A2 // o2 sensor 16 pin analog




#define tempSensors 22 // both temperature sensors digital 
#define probePump 23
#define antifoam 24
#define heaterRelay 25 // heater relay digital 

OneWire oneWire(tempSensors);
DallasTemperature tempSensorsOneWire(&oneWire);
byte tempInsideSensorAdress[8] = {0x28, 0x18, 0x12, 0x43, 0xD4, 0xE1, 0x3C, 0x58}; // ten z kablami 
byte tempOutsideSensorAdress[8] = {0x28, 0x9C, 0xE4, 0x43, 0xD4, 0xE1, 0x3C, 0x54}; // trytytka 


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
  
}




void loop() {
  
  
  
  
  //=========================================== INPUT READ ==================================================
  sampleSignal = 0;
  commentOutput = "test_comment";
  isRunning = 1;
  
  if (Serial.available() > 0) {
    // Read the input from the serial port until a newline character is encountered
    String input = Serial.readStringUntil('\n');
    input.trim(); // Remove any trailing newline characters


    int count = 0;
    // Split the string
    String* input_arr = splitString(input, ',', count);


    // Convert the strings to appropriate types
    tempInput = input_arr[0].toFloat();
    phInput = input_arr[1].toFloat();
    stirRPM = input_arr[2].toInt();
    antifoamInput = input_arr[3].toInt();
    airRpmInput = input_arr[4].toInt();
    isRunning = input_arr[5].toInt();
    sampleSignal = input_arr[6].toInt();
    stopSignal = input_arr[7].toInt();


    // Free the allocated memory
    delete[] input_arr;


    // Print the input array for debugging
    //Serial.println(isRunning);


    // communicate about process start
    if (isRunning == 1) {
      // Start the process
      commentOutput+="Process running ";
      cycleStartTime = millis();


    } else if (isRunning == 0) {
      // Pause the process


      //Calculate process time
      cycleEndTime = millis();
      totalCycleTime = totalCycleTime + (cycleEndTime - cycleStartTime);
     
      commentOutput += "Process paused total Cycle time:";
      commentOutput += totalCycleTime;
      
    }


  }
  













  
    // ================================================ MAIN LOOP IF isRunning =============================
    if (isRunning == 1) {
      // WHOLE RUNNING CODE
    



    //Temperature measurement and update 
     tempSensorsOneWire.requestTemperatures();
     tempInsideOutput = tempSensorsOneWire.getTempC(tempInsideSensorAdress);
     tempOutsideOutput = tempSensorsOneWire.getTempC(tempOutsideSensorAdress);
    //Place for PH measurement and update 

    // Place for O2 sensor measurement and update 
    //digitalWrite(probePumpSuck, LOW);
   // digitalWrite(probePump, HIGH);

    
     // engineStartStop(airPump, 255);
      //delay(4000);
      //engineStartStop(airPump, 0);
     // delay(1000);

//============================ heater ==================== 


tempOutsideOutput = 25;
//tempInput = 30; 
     

     if(tempOutsideOutput >= tempInput){
      digitalWrite (heaterRelay, HIGH) ; // HIGH MEANS HEATER IS OFF!!! 
      }
      else if(tempOutsideOutput < tempInput){
      digitalWrite (heaterRelay, LOW) ; // LOW MEANS HEATER IS ON!!! 
        }



//====================== SAMPLE ================
sampleSignal = 4;
    if(sampleSignal == 0){
      }
               
     else if (sampleSignal == 1){
      digitalWrite(probePump, HIGH); //18
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
     
//============================================

      //time = millis();
      //Serial.println(time);    
      delay(3000);

// ==================================== arduino output to rasbery
    commentOutput += "isRunning: ";
    commentOutput += isRunning;
    Serial.print(totalCycleTime);
    Serial.print(",");
    Serial.print(tempInsideOutput);
    Serial.print(",");
    Serial.print(tempOutsideOutput);
    Serial.print(",");
    Serial.print(phValueOutput);
    Serial.print(",");
    Serial.print(o2ValueOutput);
    Serial.print(",");
    Serial.print(antifoamOutput);
    Serial.print(",");
    Serial.print(stirRPM);
    Serial.print(",");
    Serial.print(airRpmInput);
    Serial.print(",");
    Serial.print(sampleSignal);
    Serial.print(",");
    Serial.print(isRunning);
    Serial.print(",");
    Serial.println(commentOutput);
    






    } else if (isRunning == 0) {
      Serial.println("is Running == 0");
      //NOTHING
   
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
