import network
import socket
import struct
from machine import Pin, ADC, I2C, PWM
import time
import bme280



#servomotor
servo_pin1 = Pin(32)
s_izquierda = PWM(servo_pin1, freq=50)
servo_pin2 = Pin(26)
s_derecha = PWM(servo_pin2, freq=50)
servo_pin3 = Pin(25)
s_cola = PWM(servo_pin3, freq=50)
motor_pin = Pin(15)
motor = PWM(motor_pin, freq=50)


#SENSOR BME280
ltemp = []
lhum = []
lpress = []


i2c_sensor = I2C(1, scl=Pin(5), sda=Pin(18))  # Ajusta los pines SCL y SDA según tu configuración
bme = bme280.BME280(i2c=i2c_sensor)

# Configuración de la red Wi-Fi
#Usurio y contraseña en cuestión

def mover_servo(servo, angulo):
    # Asegurarse de que el ángulo esté en el rango permitido
    if angulo < 0:
        angulo = 0
    elif angulo > 200:
        angulo = 200
    
    # Convertir el ángulo a un rango de ciclo de trabajo
    min_pulse = 1000  # Valor mínimo del pulso (us)
    max_pulse = 2000  # Valor máximo del pulso (us)
    pulse_width = min_pulse + (angulo / 180) * (max_pulse - min_pulse)
    
    # Convertir a ciclo de trabajo de 16 bits (0-65535)
    duty = int((pulse_width / 20000) * 65535)
    servo.duty_u16(duty)
    
def set_angle(angle):
    velocidad = 40 + (angle / 180) * 115  # Mapeo de ángulo a duty cycle
    motor.duty(int(velocidad))
    

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(ssid, password)


while not sta.isconnected():
    pass

print('Conectado. IP:', sta.ifconfig()[0])

# Configuración del puerto para recibir datos
server_port = 8081
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', server_port))
server_socket.listen(1)
server_socket.settimeout(5)  # Tiempo de espera de 5 segundos


# Configuración para enviar datos al ESP32 A
client_ip = '192.168.251.108'  # Reemplaza con la IP del ESP32 A
client_port = 8080


while True:
    start_time = time.time()
    connected = False
    print("Esperando conexión...")

    # Esperar una conexión por un tiempo máximo de 5 segundos
    while not connected:
        if time.time() - start_time > 5:  # Tiempo de espera de 5 segundos
            print("Tiempo de espera alcanzado, intentando de nuevo...")
            break
        try:
            cl, addr = server_socket.accept()  # Intentar aceptar la conexión
            connected = True
            print('Cliente conectado desde', addr)
        except OSError as e:
            pass  # No se ha establecido una conexión aún, continuar esperando

    if connected:
        while True:
            data = cl.recv(8)  # Recibir datos
            if not data:
                break
            x1, y1, x2, y2 = struct.unpack('HHHH', data)
            #print("Recibido de ESP32 A - motor:", x1, "alas:", y1, "cola:", x2, "boton:", y2)
            
            #control de los servos de las alas
            if y1 > 3000:
                mover_servo(s_izquierda, 200)
                mover_servo(s_derecha, 10)
            elif y1 < 1200:
                mover_servo(s_izquierda, 10)
                mover_servo(s_derecha, 200)
            else:
                mover_servo(s_izquierda, 10)
                mover_servo(s_derecha, 10)
                
            #control de los servos de la cola
            if x2 > 3000:
                mover_servo(s_cola, 190)
            elif x2 < 1200:
                mover_servo(s_cola, 0)
            #control velocidad del motor
            if x1>2500:
                set_angle(40)
            else:
                set_angle(0)

            cl.send(b"Datos recibidos")

        cl.close()

    # Enviar datos al ESP32 A
    s = socket.socket()
    try:
        s.connect((client_ip, client_port))
        # Leer los valores del sensor BME280
        temperature, pressure, humidity = bme.read_compensated_data()
        
        # Convertir los datos a valores legibles
        temperature //= 100  # Temperatura en grados Celsius
        pressure //= 100  # Presión en hectopascales (hPa)
        humidity //= 1024# Humedad relativa en porcentaje
        print(temperature, pressure,humidity)

        # Empaquetar los datos en un formato binario
        datos = struct.pack('fff', temperature, pressure,humidity)
        s.send(datos)
        
        
        response = s.recv(1024)
        print('Respuesta del servidor:', response)
        
    except OSError as e:
        print("Error de conexión:", e)
        
    finally:
        s.close()

    #time.sleep(0.5)