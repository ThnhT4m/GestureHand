


#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

// ===== WIFI =====
const char* ssid     = "NAME YOUR WIFI";
const char* password = "PASS YOUR WIFI";

// ===== UDP =====
WiFiUDP udp;
const int UDP_PORT = 4210;
char incomingPacket[255];

// ===== SERVO CONFIG =====
const int LEDC_FREQ    = 50;
const int LEDC_RES     = 16;
const int PULSE_MIN_US = 500;
const int PULSE_MAX_US = 2500;

// 7 servo: thumb1, thumb2, index, middle, ring, pinky, wrist
const int servoPins[7] = {18, 16, 19, 21, 22, 17, 25};
const int channels[7]  = { 0,  1,  2,  3,  4,  5,  6};

bool invert[7] = {
  false, // thumb1
  false, // thumb2
  false, // index
  true,  // middle
  false, // ring
  true,  // pinky
  false  // wrist (360)
};

// ===== BIẾN TOÀN CỤC =====
int currentAngle[7] = {90, 90, 90, 90, 90, 90, 90};
int targetAngle[7]  = {90, 90, 90, 90, 90, 90, 90};

// ===== FUNCTION =====
uint32_t angleToDuty(int angle) {
  int pulseWidth = map(angle, 0, 180, PULSE_MIN_US, PULSE_MAX_US);
  return (pulseWidth * 65535) / 20000;
}

void servoWrite(int ch, int angle) {
  ledcWrite(ch, angleToDuty(angle));
}

// ===== SMOOTH =====
void smoothMove(int ch, int target) {
  int &cur = currentAngle[ch];
  if (cur < target)      cur += 3;
  else if (cur > target) cur -= 3;
  servoWrite(ch, cur);
}

// ===== SETUP =====
void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  udp.begin(UDP_PORT);

  for (int i = 0; i < 7; i++) {
    ledcSetup(channels[i], LEDC_FREQ, LEDC_RES);
    ledcAttachPin(servoPins[i], channels[i]);
    servoWrite(i, currentAngle[i]);
  }
}

// ===== LOOP =====
void loop() {
  // ===== NHẬN UDP =====
  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(incomingPacket, 255);
    if (len > 0) incomingPacket[len] = 0;
    Serial.println(incomingPacket);

    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, incomingPacket);

    if (!error) {
      int thumb1 = doc["thumb1"];
      int thumb2 = doc["thumb2"];
      int index  = doc["index"];
      int middle = doc["middle"];
      int ring   = doc["ring"];
      int pinky  = doc["pinky"];
      int wrist = doc["wrist"]; 
        servoWrite(6, wrist);   

      // ===== MAPPING =====
      targetAngle[0] = thumb1 / 2; // 0–180 → 0–90
      targetAngle[1] = thumb2 / 2; // 0–180 → 0–90
      targetAngle[2] = index;
      targetAngle[3] = middle;
      targetAngle[4] = ring;
      targetAngle[5] = pinky;
      // Servo 360: 0→60(lui), 180→120(tới), 90=dừng
 

      // ===== INVERT =====
      for (int i = 0; i < 7; i++) {
        if (invert[i]) targetAngle[i] = 180 - targetAngle[i];
      }

      // ===== SAFETY =====
      for (int i = 0; i < 7; i++) {
        targetAngle[i] = constrain(targetAngle[i], 0, 180);
      }
    } else {
      Serial.println("JSON parse failed");
    }
  }

  // ===== LUÔN CHẠY SMOOTH =====
  for (int i = 0; i < 7; i++) {
    smoothMove(i, targetAngle[i]);
  }
  delay(20); // ~50Hz
}
