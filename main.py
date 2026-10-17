import os
from dotenv import load_dotenv
from pwdlib import PasswordHash
from fastapi import HTTPException, status, FastAPI, Depends
from pydantic import BaseModel, Field
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from datetime import datetime, timezone, timedelta
import jwt
from jwt.exceptions import InvalidTokenError
 
load_dotenv()
 
app= FastAPI(title="Campus API segura")
 
CLAVE_SECRETA = os.getenv("JWT_SECRET_KEY")
ALGORITMO = "HS256"
MINUTOS_EXPIRACION = 60
 
if not CLAVE_SECRETA:
    raise RuntimeError("No esta configurada la clase secreta de JWT en el .env")
 
usuarios_db={}
 
contexto_password = PasswordHash.recommended()
 
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="token")
 
class UsuarioRegistro(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
 
class RespuestaToken(BaseModel):
    access_token: str
    token_type: str
 
def hashear_password(password: str)->str:
    return contexto_password.hash(password)
 
def verificar_password(password: str, hash_guardado: str)->bool:
    return contexto_password.verify(password,hash_guardado)
 
 
@app.post("/usuarios/registro", status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario:UsuarioRegistro):
 
    if usuario.username in usuarios_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="El usuario ya existe")
 
    usuarios_db[usuario.username]={
        "username":usuario.username,
        "password_hash":hashear_password(usuario.password)
    }
 
    return{
        "mensaje":"Usuario registrado correctamente",
        "username":usuario.username,
        "password":usuarios_db
    }
 
def crear_token_acceso(username:str)->str:
    expiracion=datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_EXPIRACION)
 
    payload = {
        "sub":username,
        "exp":expiracion,
    }
 
    return jwt.encode(payload, CLAVE_SECRETA, algorithm=ALGORITMO)
 
@app.post("/token",response_model=RespuestaToken)
def iniciar_sesion(formulario: OAuth2PasswordRequestForm = Depends()):
    usuario = usuarios_db.get(formulario.username)
 
    if not usuario or not verificar_password(formulario.password, usuario["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )
 
    token = crear_token_acceso(usuario["username"])
    return{
        "access_token":token,
        "token_type":"bearer"
    }
 
 
def obtener_usuario_actual(token: str = Depends(esquema_oauth2))->dict:
    try:
        payload = jwt.decode(
            token,
            CLAVE_SECRETA,
            algorithms=[ALGORITMO],
            options={"require": ["sub","exp"]}
        )
        username = payload.get("sub")
 
        if not isinstance(username, str) or not username:
            raise ValueError("Token sin usuario valido")
    except(InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate":"Bearer"}
        )
 
    usuario = usuarios_db.get(username)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate":"Bearer"}
        )
    return usuario
 
@app.get("/publico")
def publico():
    return{
        "mensaje":"Bienvenido a Campus API"
    }
 
@app.get("/perfil")
def obtener_perfil(usuario_actual: dict = Depends(obtener_usuario_actual)):
    return{
        "mensaje": "Acceso authorizado",
        "username": usuario_actual["username"]
    }
 
@app.get("/cursos")
def cursos(usuario_actual: dict = Depends(obtener_usuario_actual)):
    return {
        "usuario":usuario_actual["username"],
        "cursos":["Python","Java","FastAPI"]
    }
 