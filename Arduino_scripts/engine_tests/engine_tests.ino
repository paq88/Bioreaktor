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


void setup() {
  // put your setup code here, to run once:
  pinMode(waterPump, OUTPUT);
  pinMode(Stirrer, OUTPUT);
  pinMode(pwmStirrer,OUTPUT);
  
}

void loop() {
digitalWrite(Stirrer, HIGH);
analogWrite(pwmStirrer,0);
  // put your main code here, to run repeatedly:
digitalWrite(waterPump, HIGH);
digitalWrite(probePump, HIGH);
digitalWrite(pwmProbePump,0);
}
