from machine import Pin, PWM
import time


motor_pin = Pin(15)
motor = PWM(motor_pin, freq=50)

def set_angle(angle):
    velocidad = 40 + (angle / 180) * 115  # Mapeo de ángulo a duty cycle
    motor.duty(int(velocidad))
    
for i in range(0, 100, 5):
    print(i)
    set_angle(i)
    time.sleep(5)