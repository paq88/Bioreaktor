// onboard screen
#include "ArduinoGraphics.h"
#include "Arduino_LED_Matrix.h"
ArduinoLEDMatrix matrix;
//





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


void setup() {
  // Onboard screen
  matrix.begin();
  //


  Serial.begin(115200);
}

// onboard screen
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
//



void loop() {
  
  
  
  
  //=========================================== INPUT READ ==================================================
  commentOutput = "test_comment";
  
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
    ON();

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
      //NOTHING
      OFF();
    }
 


  delay(1000);
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


