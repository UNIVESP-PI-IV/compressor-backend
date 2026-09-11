from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'compressor_db'
}

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
                
                # Extrai a temperatura do JSON
                temperature = data.get('temperature')

                if temperature is None:
                    print("Campo 'temperature' ausente no payload.")
                    self._send_response(422, {'status': 'error', 'message': 'Missing temperature field'})
                    return
                
                # Insere o registro no MySQL
                connection = mysql.connector.connect(**DB_CONFIG)
                cursor = connection.cursor()
                
                query = "INSERT INTO readings (temperature) VALUES (%s)"
                cursor.execute(query, (temperature,))
                
                connection.commit()
                cursor.close()
                connection.close()
                
                print(f"Sucesso! Temperatura de {temperature}°C salva no banco de dados.")
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
        self.send_response(statusCode)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))


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