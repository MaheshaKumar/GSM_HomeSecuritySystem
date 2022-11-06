#include "ESP8266WiFi.h"
#include <WiFiUdp.h>
const char* ssid = "GsmSecurityRouter"; //Enter SSID
const char* password = "gsmsecurity123"; //Enter Password
WiFiUDP udp;
int doorState;
const int door = 0;
const int LED = 2;// Assigning Pin 4 as the name LED
int previousState = LOW;
int currentState = LOW;
struct packet_frame
{
  uint8_t header;
  uint8_t doorState;
  uint8_t footer;
};
enum doorState
{
  CLOSE = 0x00,
  OPEN = 0x01
};
struct packet{
  packet_frame frame;
  size_t size;
};
const uint8_t DATASIZE = 3;
packet data = {0};
void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
   pinMode (door, INPUT_PULLUP);
   pinMode(LED,OUTPUT);// Declaring LED pin as an output.
   digitalWrite(LED,LOW);
   WiFi.begin(ssid, password);
   int count = 0;
   while ((WiFi.status() != WL_CONNECTED) && count < 10) 
    {
       delay(500);
       Serial.print("*");
       count++;
    }
    if( WiFi.status() == WL_CONNECTED)
    {
      Serial.println("WiFi connection Successful");
      Serial.print("The IP Address of ESP8266 Module is: ");
      Serial.print(WiFi.localIP());// Print the IP address
    }
    data.frame.header = 0xFF;
    data.frame.doorState = 0x00;
    data.frame.footer = 0xFA;
    data.size = DATASIZE;

}

void loop () // Code under this loop runs forever.
{
    int count = 0;
    while ((WiFi.status() != WL_CONNECTED) && count < 3) 
    {
       WiFi.begin(ssid, password);
       delay(500);
       Serial.print("*");
       count++;
    }    
    previousState = currentState;
    currentState = digitalRead(door); // read state    
    if (currentState == HIGH) { // state change: LOW -> HIGH
      data.frame.doorState = OPEN;      
      Serial.println("The door-opening event is detected");
      digitalWrite(LED,HIGH);
      // TODO: turn on alarm, light or send notification ...
    }
    else
    if (currentState == LOW) { // state change: HIGH -> LOW
      data.frame.doorState = CLOSE;
      Serial.println("The door-closing event is detected");
      digitalWrite(LED,LOW);
      // TODO: turn off alarm, light or send notification ...
    } 
    uint8_t bytes[DATASIZE] = {0};
    memcpy(&bytes,&data.frame,sizeof(bytes));
    udp.beginPacket("192.168.4.110", 12000);
    udp.write(bytes,data.size);
    Serial.println(WiFi.localIP());
    udp.endPacket();
    delay(1500);            
}
