# Campus API

API desarrollada con FastAPI para registrar usuarios, iniciar sesión con tokens JWT y consultar recursos protegidos.

## Tecnologías

- FastAPI y Pydantic para la API y la validación de datos.
- PyJWT para tokens firmados con HS256.
- pwdlib con Argon2 para el hash de contraseñas.
- python-dotenv para cargar la configuración desde `.env`.

## Instalación en Windows (PowerShell)

Necesitas Python y pip instalados. El proyecto no declara una versión mínima de Python ni fija versiones de sus dependencias.

```powershell
cd 'C:\Users\Usuario\Documents\ultimos py'
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Los comandos usan directamente el Python del entorno virtual, por lo que no hace falta activarlo.

## Configuración

Si todavía no tienes un archivo `.env`, créalo a partir del ejemplo:

```powershell
Copy-Item .env.example .env
```

Genera una clave secreta:

```powershell
.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Edita `.env` y asigna el valor generado:

```dotenv
JWT_SECRET_KEY=REEMPLAZA_ESTO_CON_LA_CLAVE_GENERADA
```

La aplicación requiere `JWT_SECRET_KEY` para iniciar. Mantén esta clave privada. El archivo `.env` está excluido del control de versiones mediante `.gitignore`.

## Ejecutar en desarrollo

Desde la carpeta del proyecto:

```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

La ruta raíz `/` no está definida. Puedes comprobar el funcionamiento en `/publico`. La opción `--reload` reinicia el servidor al cambiar el código y se utiliza para desarrollo.

## Endpoints

| Método | Ruta | Autenticación | Descripción |
| --- | --- | --- | --- |
| POST | `/usuarios/registro` | No | Registra un usuario con un cuerpo JSON. |
| POST | `/token` | No | Recibe credenciales como formulario y devuelve un token. |
| GET | `/publico` | No | Devuelve un mensaje de bienvenida. |
| GET | `/perfil` | Bearer JWT | Devuelve el nombre del usuario autenticado. |
| GET | `/cursos` | Bearer JWT | Devuelve el usuario y la lista fija de cursos: Python, Java y FastAPI. |

El nombre de usuario debe tener entre 3 y 50 caracteres y la contraseña, al menos 8. Los tokens vencen a los 60 minutos.

## Probar el flujo completo

Con el servidor en ejecución, abre otra terminal de PowerShell.

### 1. Registrar un usuario

```powershell
$registro = @{
    username = 'estudiante'
    password = 'EjemploSeguro123!'
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
    -Uri 'http://127.0.0.1:8000/usuarios/registro' `
    -ContentType 'application/json' `
    -Body $registro
```

Un registro correcto devuelve HTTP 201. Si el usuario ya existe, devuelve HTTP 409.

### 2. Obtener un token

```powershell
$sesion = Invoke-RestMethod -Method Post `
    -Uri 'http://127.0.0.1:8000/token' `
    -ContentType 'application/x-www-form-urlencoded' `
    -Body @{ username = 'estudiante'; password = 'EjemploSeguro123!' }

$token = $sesion.access_token
```

La respuesta contiene `access_token` y `token_type` con el valor `bearer`. Las credenciales incorrectas producen HTTP 401.

### 3. Consultar recursos protegidos

```powershell
$cabeceras = @{ Authorization = "Bearer $token" }

Invoke-RestMethod -Uri 'http://127.0.0.1:8000/perfil' -Headers $cabeceras
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/cursos' -Headers $cabeceras
```

También puedes usar Swagger UI: registra un usuario y pulsa **Authorize** para introducir sus credenciales. Swagger obtiene el token mediante `/token` y lo incluye en las consultas protegidas.

## Estructura

```text
main.py            Aplicación, modelos, autenticación y endpoints.
requirements.txt   Dependencias de Python.
.env.example       Plantilla de configuración sin credenciales reales.
.gitignore         Exclusiones para Git.
README.md          Instrucciones del proyecto.
```

## Limitaciones actuales

- Los usuarios se almacenan en el diccionario `usuarios_db`, en memoria. Se pierden al reiniciar el proceso, incluso con una recarga del servidor, y no se comparten entre varios procesos.
- La respuesta de `/usuarios/registro` incluye actualmente el diccionario completo de usuarios y sus hashes bajo la propiedad `password`. Debe eliminarse ese campo antes de exponer la API a terceros.
- No hay endpoints para cerrar sesión o renovar tokens ni un mecanismo de revocación.
- No se incluye una suite de pruebas automatizadas. El flujo anterior permite una comprobación manual básica.
