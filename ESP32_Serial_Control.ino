#define LED_PIN 2
#define BUZZER_PIN 25

String command = "";

bool emergencyActive = false;
bool buzzerState = false;
unsigned long lastToggle = 0;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  Serial.begin(115200);

  Serial.println("Patient Assistance System Ready");
  Serial.println("Commands: ATTENTION, EMERGENCY, CLEAR");
}

void loop() {
  // Receive commands from the computer
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();
    command.toUpperCase();

    if (command == "ATTENTION") {
      emergencyActive = false;

      digitalWrite(LED_PIN, HIGH);
      digitalWrite(BUZZER_PIN, HIGH);
      delay(300);

      digitalWrite(LED_PIN, LOW);
      digitalWrite(BUZZER_PIN, LOW);

      Serial.println("Attention alert triggered");
    }

    else if (command == "EMERGENCY") {
      emergencyActive = true;
      lastToggle = millis();

      digitalWrite(LED_PIN, HIGH);
      digitalWrite(BUZZER_PIN, HIGH);
      buzzerState = true;

      Serial.println("Emergency alert active");
    }

    else if (command == "CLEAR" ||
             command == "STOP") {
      emergencyActive = false;
      buzzerState = false;

      digitalWrite(LED_PIN, LOW);
      digitalWrite(BUZZER_PIN, LOW);

      Serial.println("Alert cleared");
    }
  }

  // Continue flashing and beeping during emergency
  if (emergencyActive &&
      millis() - lastToggle >= 200) {

    lastToggle = millis();
    buzzerState = !buzzerState;

    digitalWrite(LED_PIN, buzzerState);
    digitalWrite(BUZZER_PIN, buzzerState);
  }
}