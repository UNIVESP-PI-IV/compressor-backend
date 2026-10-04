from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
import mysql.connector

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3308,
    'user': 'root',
    'password': '',
    'database': 'compressor_db'
}

# Calibração inicial estimada a partir dos três pacotes enviados com o sensor
# parado (excluindo a primeira leitura, que aparenta ser um pico transitório).
# Subtraímos o offset de cada eixo para que a posição de repouso fique próxima
# de zero. Refaça essa média com várias leituras estáveis se o sensor mudar de
# posição, unidade ou montagem.
VIBRATION_ZERO_OFFSETS = {
    'x': -0.00048828125,
    'y': 0.0152994791667,
    'z': 0.0231119791667,
}

# Valores corrigidos abaixo deste limite são tratados como ruído de repouso.
# O limite usa a mesma unidade enviada pelo ESP32; vibrações menores que ele
# também serão zeradas, portanto ajuste-o conforme a sensibilidade desejada.
VIBRATION_NOISE_FLOOR = 0.01

class ApiRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path == '/api/compressor':
            content_length = int(self.headers.get('Content-Length', 0))
            
            if content_length == 0:
                self._send_response(400, {'status': 'error', 'message': 'Empty payload'})
                return

            body_bytes = self.rfile.read(content_length)
            body_text = body_bytes.decode('utf-8')
            
            print(f"Dados brutos recebidos: {body_text}")
            
            try:
                data = json.loads(body_text)
                
                temperature = data.get('temperature')
                vibration = data.get('vibration')

                if temperature is None:
                    print("Campo 'temperature' ausente no payload.")
                    self._send_response(422, {'status': 'error', 'message': 'Missing temperature field'})
                    return

                if not isinstance(vibration, dict) or any(axis not in vibration for axis in ('x', 'y', 'z')):
                    print("Campos de vibração incompletos no payload.")
                    self._send_response(422, {'status': 'error', 'message': 'Missing vibration fields'})
                    return

                # Remove o desvio de repouso calibrado e elimina pequenas
                # oscilações residuais antes de calcular RMS e salvar os eixos.
                accel_x = float(vibration['x']) - VIBRATION_ZERO_OFFSETS['x']
                accel_y = float(vibration['y']) - VIBRATION_ZERO_OFFSETS['y']
                accel_z = float(vibration['z']) - VIBRATION_ZERO_OFFSETS['z']
                accel_x = 0.0 if abs(accel_x) < VIBRATION_NOISE_FLOOR else accel_x
                accel_y = 0.0 if abs(accel_y) < VIBRATION_NOISE_FLOOR else accel_y
                accel_z = 0.0 if abs(accel_z) < VIBRATION_NOISE_FLOOR else accel_z
                rms = math.sqrt((accel_x ** 2 + accel_y ** 2 + accel_z ** 2) / 3) 
                
                # Insere o registro no MySQL
                connection = mysql.connector.connect(**DB_CONFIG)
                cursor = connection.cursor()
                
                query = """
                    INSERT INTO readings
                        (temperature, accel_x, accel_y, accel_z, rms)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query, (temperature, accel_x, accel_y, accel_z, rms))
                
                connection.commit()
                cursor.close()
                connection.close()
                
                print(f"Sucesso! Temperatura de {temperature}°C e vibração RMS de {rms} salvas no banco de dados.")
                self._send_response(201, {'status': 'success', 'message': 'Telemetry recorded'})
                
            except json.JSONDecodeError:
                print("Erro: JSON inválido recebido no corpo da requisição.")
                self._send_response(400, {'status': 'error', 'message': 'Invalid JSON'})
            except mysql.connector.Error as db_err:
                print(f"Erro no banco de dados MySQL: {db_err}")
                self._send_response(500, {'status': 'error', 'message': 'Database insertion failed'})
            except Exception as err:
                print(f"Erro inesperado: {err}")
                self._send_response(500, {'status': 'error', 'message': 'Internal server error'})
        else:
            print(f"Rota não encontrada: {self.path}")
            self._send_response(404, {'status': 'error', 'message': 'Endpoint not found'})

    def _send_response(self, statusCode, payload):
        response_bytes = json.dumps(payload).encode('utf-8')
        
        self.send_response(statusCode)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.send_header('Connection', 'close')
        self.end_headers()
        
        self.wfile.write(response_bytes)
        self.wfile.flush()


def run_server():
    server_address = ('0.0.0.0', 8000)
    httpd = HTTPServer(server_address, ApiRequestHandler)
    print("Servidor de Telemetria do Compressor rodando na porta 8000...")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n Servidor encerrado com sucesso.")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
