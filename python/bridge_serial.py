import serial
import time
from cassandra.cluster import Cluster
from datetime import datetime

# --- CONFIGURACIÓN DEL NÚCLEO (AUDITORÍA) ---
PORT = '/dev/ttyACM0'  # Asegúrate de que sea este con 'ls /dev/ttyACM*'
BAUD_RATE = 9600
KEYSPACE = 'hidroponia_store'

def start_bridge():
    cluster = None
    try:
        # 1. Conexión a Cassandra (Docker en SSD)
        cluster = Cluster(['127.0.0.1'], port=9042)
        session = cluster.connect(KEYSPACE)
        print(f"[OK] Conectado a Cassandra en el SSD.")

        # 2. Conexión al Hardware (Arduino)
        arduino = serial.Serial(PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Espera para inicialización
        print(f"[OK] Escuchando puerto {PORT}...")

        while True:
            if arduino.in_waiting > 0:
                # Lectura: recibe "24.50,60.00,6.50,85.00"
                line = arduino.readline().decode('utf-8').strip()
                
                if line:
                    parts = line.split(',')
                    if len(parts) == 4:
                        try:
                            valores = [float(p) for p in parts]
                            # Nombres sincronizados con FastAPI
                            nombres = ["Temperatura", "Humedad", "pH", "Luz"] 
                            ahora = datetime.now()

                            for i in range(4):
                                query = """
                                INSERT INTO sensor_data (sensor_id, fecha_hora, tipo_sensor, valor)
                                VALUES (%s, %s, %s, %s)
                                """
                                session.execute(query, (nombres[i], ahora, "Analogico", valores[i]))
                            
                            print(f"[DATOS] {ahora.strftime('%H:%M:%S')} - Guardado: {parts}")
                        
                        except ValueError:
                            print(f"[ERROR] Datos corruptos recibidos: {line}")
                    else:
                        print(f"[AVISO] Trama incompleta: {line}")

    except serial.SerialException:
        print(f"[CRÍTICO] No se pudo acceder al puerto {PORT}. ¿Está conectado el Arduino?")
    except KeyboardInterrupt:
        print("\n[INFO] Deteniendo puente de datos.")
    except Exception as e:
        print(f"[ERROR SISTEMA] {e}")
    finally:
        if cluster:
            cluster.shutdown()
            print("[INFO] Conexión a Cassandra cerrada.")

if __name__ == "__main__":
    start_bridge()