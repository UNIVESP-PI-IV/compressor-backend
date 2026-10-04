# Compressor Backend

Backend em Python que recebe do ESP32 a temperatura e a vibração nos eixos X, Y e Z. Calcula o RMS da vibração corrigida e armazena as leituras em um banco MySQL ou MariaDB.

## Requisitos

- Python 3.10 ou superior
- MySQL ou MariaDB em execução
- Dependências Python listadas em `requirements.txt`

## Configurar o banco

O esquema do banco está em `database/schema.sql`. Execute essa migration no banco de dados antes de iniciar a API. O exemplo abaixo considera o MySQL na porta `3306`; ajuste host, porta e usuário se necessário.

Depois, crie o arquivo local `.env` a partir do modelo e informe os dados de conexão. O `.env` é ignorado pelo Git; não inclua credenciais reais no `.env.example`.

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=compressor_db
```

## Windows (PowerShell)

Na raiz do projeto:

```powershell
python -m venv .venv
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
Get-Content -Raw database\schema.sql | mysql.exe --host=127.0.0.1 --port=3306 --user=root --password
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

O comando `mysql.exe` pressupõe que o cliente MySQL esteja no `PATH`. Se não estiver, use o caminho completo do executável instalado.

## Linux

Na raiz do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
test -f .env || cp .env.example .env
nano .env
mysql --host=127.0.0.1 --port=3306 --user=root --password < database/schema.sql
python -m pip install -r requirements.txt
python main.py
```

## API

O servidor escuta na porta `8000`. O ESP32 deve enviar um `POST` para `/api/compressor` com um JSON neste formato:

```json
{
  "temperature": 34.8,
  "vibration": {
    "x": 0.01,
    "y": 0.02,
    "z": 0.03
  }
}
```

Na configuração do ESP32, use o endereço IP do computador que executa o backend, por exemplo `http://192.168.1.10:8000/api/compressor`. Para encerrar o servidor, pressione `Ctrl+C` no terminal.
