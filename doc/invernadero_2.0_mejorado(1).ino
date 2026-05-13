#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

// -------- LCD --------
LiquidCrystal_I2C lcd(0x27,20,4);
LiquidCrystal_I2C lcd_1(39, 16, 2);

// -------- DHT22 --------
#define dataPin 6
#define DHTType DHT22
DHT dht(dataPin, DHTType);

// -------- VARIABLES --------
float TEMPERATURA = 0;
int HUMEDAD = 0;

void setup()
{
  Serial.begin(9600);

  // LCDs
  lcd.init();
  lcd.backlight();

  lcd_1.init();
  lcd_1.backlight();

  // Pines
  pinMode(A0, INPUT);
  pinMode(A1, INPUT);

  // Sensor
  dht.begin();

  // Mensaje inicial
  lcd.setCursor(0,0);
  lcd.print("Invernadero...");
}

void loop()
{
  // -------- LECTURA DHT22 --------
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  // -------- SI FALLA EL SENSOR --------
  if (isnan(h) || isnan(t)) {
    Serial.println("Error DHT22");

    lcd.setCursor(0,0);
    lcd.print("Error DHT22      ");
    lcd.setCursor(0,1);
    lcd.print("Revisar sensor   ");

    lcd_1.setCursor(0,0);
    lcd_1.print("Error sensor     ");
    lcd_1.setCursor(0,1);
    lcd_1.print("DHT22            ");

    delay(2000);
    return;
  }

  // -------- TEMPERATURA REAL --------
  TEMPERATURA = t;

  // -------- HUMEDAD ANALOGICA --------
  HUMEDAD = map(analogRead(A1), 0, 1023, 0, 100);

  // -------- LCD PEQUEÑO --------
  lcd_1.setCursor(0, 0);
  lcd_1.print("TEMP=");
  lcd_1.setCursor(6, 0);
  lcd_1.print(TEMPERATURA);
  lcd_1.print("C   ");

  lcd_1.setCursor(0, 1);
  lcd_1.print("HUM=");
  lcd_1.setCursor(6, 1);
  lcd_1.print(HUMEDAD);
  lcd_1.print("%   ");

  // -------- LCD GRANDE --------
  lcd.setCursor(0,0);
  lcd.print("Temp:");
  lcd.setCursor(6,0);
  lcd.print(TEMPERATURA);
  lcd.print("C   ");

  lcd.setCursor(0,1);
  lcd.print("Hum:");
  lcd.setCursor(6,1);
  lcd.print(h);
  lcd.print("%   ");

  // -------- CONTROL TEMPERATURA --------
  if (TEMPERATURA <= 10) {
    Serial.println("FRIO (<=10C)");
  } 
  else if (TEMPERATURA >= 30) {
    Serial.println("CALOR (>=30C)");
  } 
  else {
    Serial.println("NORMAL");
  }

  // -------- SERIAL --------
  Serial.print("Temp: ");
  Serial.print(TEMPERATURA);
  Serial.print(" C | Hum: ");
  Serial.print(h);
  Serial.println(" %");

  delay(2000);
}