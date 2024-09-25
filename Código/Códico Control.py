import network
import socket
import struct
from machine import Pin, ADC, I2C
import ssd1306
import time

#pantalla oled
i2c_oled = I2C(scl=Pin(12), sda=Pin(14))  # Ajusta los pines SCL y SDA según tu configuración

oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c_oled)

# Configuración de los pines y los joysticks
joystick_x1 = ADC(Pin(34))  # Pin analógico para el eje X del primer joystick
joystick_y1 = ADC(Pin(35))  # Pin analógico para el eje Y del primer joystick
joystick_x2 = ADC(Pin(32))  # Pin analógico para el eje X del segundo joystick
sw = Pin(33, Pin.IN, Pin.PULL_UP)

joystick_x1.atten(ADC.ATTN_11DB)
joystick_y1.atten(ADC.ATTN_11DB)
joystick_x2.atten(ADC.ATTN_11DB)


# Configuración de la red Wi-Fi
#ssid = 'HONOR X8'
#password = 'Jorgentas231'
#ssid = 'Movistar'
#password = '97865432'
#ssid = 'Galaxy'
#password = 'Sebastian123'
ssid = 'FAMILIA CORTES'
password = 'marcedigu36'

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(ssid, password)

while not sta.isconnected():
    pass

print('Conectado. IP:', sta.ifconfig()[0])

# Configuración del puerto para recibir datos
server_port = 8080
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', server_port))
server_socket.listen(1)
server_socket.settimeout(5)  # Tiempo de espera de 5 segundos


# Configuración para enviar datos al ESP32 B
client_ip = '192.168.20.65'  # Reemplaza con la IP del ESP32 B
client_port = 8081

def datos_oled(var1, var2, var3):
    oled.fill(0)
    oled.text("temp:", 0, 0)
    oled.text("C", 90, 0)
    oled.text(str(var1), 50, 0)
    oled.text("hum:", 0, 20)
    oled.text(str(var2), 40, 20)
    oled.text("%", 70, 20)
    oled.text("press:", 0, 40)
    oled.text(str(var3), 50, 40)
    oled.show()
    
def limpiar():
    oled.fill(0)
    oled.show()

vacia = True

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
            data = cl.recv(12)  # Recibir datos
            if not data:
                break
            temperatura, presion, humedad = struct.unpack('fff', data)
            print("Recibido de ESP32 B - temperatura", temperatura, "humedad", humedad, "presion", presion)
            cl.send(b"Datos recibidos")
        cl.close()


    # Enviar datos al ESP32 B
    s = socket.socket()
    try:
        s.connect((client_ip, client_port))
        # Leer los valores de los joysticks
        motor = joystick_x1.read()
        alas = joystick_y1.read()
        cola = joystick_x2.read()
        boton = sw.value()
        
        
        # Empaquetar los datos en un formato binario
        datos = struct.pack('HHHH', motor, alas, cola, boton)
        s.send(datos)
        
        response = s.recv(1024)
        print('Respuesta del servidor:', response)
    except OSError as e:
        print("Error de conexión:", e)
    finally:
        s.close()

    if sw.value() == 0:
        if vacia:
            datos_oled(temperatura, humedad, presion)
            vacia = False
        else:
            limpiar()
            vacia = True
        
    #time.sleep(0.5)