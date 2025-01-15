
#include "OneWire.h"
#include "DallasTemperature.h"




int isRunning = 0;
float tempInput; // Temperature we want
float tempInsideOutput; // Temperature we have inside
float tempOutsideOutput; // Temperature we have outside
int phInputSignal; // signal to add alkali/acid  --- 0 - nothing, 1-add drop of acid 2- add drop of alkali 

// ph 
// calibration coeficients
float b_ph0 = 15.169377;
float b_ph1 = -0.025857;
// calibration coeficients o2
float b_o2_0 = -2.5641  ;
float b_o2_1 = 0.05128  ;

float phValueOutput; // pH we have
float phVoltage; // voltage from pH probe

//o2
float o2Voltage; // voltage from o2 sensor 
float o2ValueOutput; //o2 we have 



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
//(subboard pins)
 
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
#define pwmAlkaliPump1 11
#define pwmStirrer 12 // speed of Stirrer (mieszadlo)
#define free13 13 // freee pwm

#define Stirrer 14
#define acidPump2 15 // peristalticPump 2
#define alkaliPump1 16 // peristalticPump 1

#define phSensor A1 //ph Sensor 15 pin analog   (13)
#define o2Sensor A2 // o2 sensor 16 pin analog  (14)




#define tempSensors 52 // both temperature sensors digital (16)


#define heaterRelay 53 // heater relay digital (11)

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
  pinMode(pwmAlkaliPump1, OUTPUT);
  pinMode(pwmStirrer, OUTPUT); 
  pinMode(acidPump2, OUTPUT);    
  pinMode(alkaliPump1, OUTPUT);
  
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
    phInputSignal = input_arr[1].toInt(); // ph input is now signal to add one drop of alkali/acid 0 - nothing 1- acid (lowers pH) 2 - alkali (ph- UP )
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
      if(totalCycleTime ==0 ){cycleStartTime = millis();}
      


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
    



    // ==================================== MOTORS ===========================
      
      digitalWrite(waterPump, HIGH);
      engineStartStop(airPump, airRpmInput);
      engineStartStop(Stirrer, stirRPM);



    //Temperature measurement and update 
     tempSensorsOneWire.requestTemperatures();
     tempInsideOutput = tempSensorsOneWire.getTempC(tempInsideSensorAdress); // z izolacja 
     tempOutsideOutput = tempSensorsOneWire.getTempC(tempOutsideSensorAdress); // z trytytka 
    //Place for PH measurement and update 

    

    
     

//============================ Temperature ==================== 



     

     if(tempOutsideOutput >= tempInput){
      digitalWrite (heaterRelay, HIGH) ; // HIGH MEANS HEATER IS OFF!!! 
      }
      else if(tempOutsideOutput < tempInput){
      digitalWrite (heaterRelay, LOW) ; // LOW MEANS HEATER IS ON!!! 
        }

//======================= PH - acid/alkali=============

// read from probe 
phVoltage = analogRead(phSensor);
phValueOutput = b_ph0 + b_ph1*phVoltage;

if(phInputSignal == 0){}
else if (phInputSignal == 1){ //drop of acid

engineStartStop(acidPump2, 255);
delay(3000);
engineStartStop(acidPump2, 0);


}
else if (phInputSignal == 2 ) { //drop  of alkali 
engineStartStop(alkaliPump1, 255);
delay(3000);
engineStartStop(alkaliPump1, 0);

}


//==========================o2==================
o2Voltage = analogRead(o2Sensor);
o2ValueOutput = b_o2_0 + (o2Voltage*5000/1024)*b_o2_1;




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

    //====================== ANTIFOAM ================




      if(antifoamInput == 0){
        engineStartStop(antifoam,0);
      }else if (antifoamInput == 1){
      engineStartStop(antifoam, 255);
      } else {
        commentOutput+=", Wrong antifoam intput: ";
        commentOutput+=antifoamInput;
        
      }




//============================================

      //time = millis();
      //Serial.println(time);    
      delay(3000);

// ==================================== arduino output to rasbery
{
    commentOutput = "isRunning: ";
    commentOutput += isRunning;
    Serial.print(totalCycleTime);
    Serial.print(",");
    Serial.print(tempInsideOutput);
    Serial.print(",");
    Serial.print(tempOutsideOutput); //  z trytytka
    Serial.print(",");
    Serial.print(phValueOutput);
    Serial.print(",");
    Serial.print(o2ValueOutput); // percentage of o2 in water (kinda)
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
    
}





    } else if (isRunning == 0) {
      //Serial.println("is Running == 0");
      digitalWrite(waterPump, LOW);
      engineStartStop(airPump, 0);
      engineStartStop(Stirrer, 0);


    digitalWrite(heaterRelay, HIGH) ; // high means OFF


    digitalWrite(probePump, LOW);
    digitalWrite(probePumpSuck, LOW);
    analogWrite(pwmProbePump, 0); 

    engineStartStop(antifoam,0);


    engineStartStop(acidPump2, 0);
    engineStartStop(alkaliPump1, 0);

      delay(3000);
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
    case alkaliPump1:
      pwmPin = pwmAlkaliPump1; 
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
