# main.py - Hakari Backend API
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import random
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
import secrets
import os
import logging

# Configuración logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hakari API",
    description="Backend para la aplicación Hakari - Personalidad 90% real con ciclo menstrual",
    version="2.0.0"
)

# CORS para app móvil
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos
class UserRegister(BaseModel):
    nombre: str
    email: str

class UserLogin(BaseModel):
    email: str

class ChatMessage(BaseModel):
    session_id: str
    message: str

# Base de datos optimizada
class HakariDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('hakari.db', check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA cache_size=10000')
        self.init_db()
    
    def init_db(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                email TEXT PRIMARY KEY,
                nombre TEXT,
                confianza INTEGER DEFAULT 30,
                interacciones INTEGER DEFAULT 0,
                energia INTEGER DEFAULT 70,
                relacion INTEGER DEFAULT 50,
                ultima_visita DATETIME,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT,
                mensaje_usuario TEXT,
                mensaje_hakari TEXT,
                estado_emocional TEXT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email TEXT,
                logro_id TEXT,
                nombre TEXT,
                descripcion TEXT,
                fecha_desbloqueo DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para mejor rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversaciones_email ON conversaciones(usuario_email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversaciones_fecha ON conversaciones(fecha)')
        
        self.conn.commit()

hakari_db = HakariDatabase()
sesiones_activas = {}

# Sistema de personalidad de Hakari
class PersonalidadHakari:
    def __init__(self):
        self.historia = {
            'nombre': 'Hakari',
            'fecha_nacimiento': date(2007, 5, 1),  # 🎂 1 de mayo 2007
            'ciudad': 'Tokyo',
            'gato': 'Mochi',
            'anime_favorito': 'Evangelion'
        }
        
        # Estados emocionales
        self.estados = {
            "feliz": {"emoji": "😊", "color": "#ec4899", "desc": "Contentita y animada"},
            "triste": {"emoji": "💔", "color": "#3b82f6", "desc": "Bajoneada y sensible"},
            "enojada": {"emoji": "🔥", "color": "#ef4444", "desc": "Molesta y cortante"},
            "cansada": {"emoji": "😴", "color": "#6b7280", "desc": "Sin energía"},
            "reflexiva": {"emoji": "🤔", "color": "#8b5cf6", "desc": "Pensativa y profunda"},
            "nostalgica": {"emoji": "📚", "color": "#6366f1", "desc": "Recordando el pasado"}
        }
        
        self.estado_actual = "reflexiva"
        self.caprichos = ["helado de matcha", "bubble tea", "leer en el parque", "ver anime"]
        self.capricho_actual = random.choice(self.caprichos)
        
        # Sistema de ciclo menstrual simplificado
        self.ciclo_menstrual = {
            'fase_actual': self.calcular_fase_actual(),
            'dolor': random.randint(0, 5)
        }

    def calcular_edad(self) -> int:
        """Calcula la edad actual de Hakari (cumpleaños: 1 de mayo)"""
        hoy = date.today()
        cumple = self.historia['fecha_nacimiento']
        
        edad = hoy.year - cumple.year
        
        # Verificar si ya pasó el cumpleaños este año
        if (hoy.month, hoy.day) < (cumple.month, cumple.day):
            edad -= 1
            
        return edad

    def es_su_cumpleanos(self) -> bool:
        """Verifica si hoy es el cumpleaños de Hakari"""
        hoy = date.today()
        cumple = self.historia['fecha_nacimiento']
        return hoy.month == cumple.month and hoy.day == cumple.day

    def calcular_fase_actual(self) -> str:
        """Calcula la fase actual del ciclo menstrual"""
        hoy = date.today()
        dia_ciclo = (hoy.day - 1) % 28 + 1
        
        if 1 <= dia_ciclo <= 5:
            return "menstruacion"
        elif 6 <= dia_ciclo <= 13:
            return "folicular"
        elif 14 <= dia_ciclo <= 16:
            return "ovulacion"
        else:
            return "lutea"

    def obtener_respuesta_rapida(self, mensaje: str, usuario_data: Dict) -> Optional[str]:
        """Respuestas predefinidas para ahorrar procesamiento"""
        mensaje_lower = mensaje.lower()
        nombre = usuario_data.get('nombre', '')
        edad = self.calcular_edad()
        
        # 🎂 Respuesta especial si es su cumpleaños
        if self.es_su_cumpleanos():
            return random.choice([
                f"¡Hoy es mi cumpleaños! 🎂 Tengo {edad} años... ¿me felicitas?",
                f"Es mi día especial... cumplo {edad} años hoy 💫",
                f"{edad} años hoy... me siento mayor 🎁"
            ])
        
        # Respuestas contextuales rápidas
        if any(palabra in mensaje_lower for palabra in ['hola', 'hi', 'hey', 'buenas']):
            return random.choice([
                f"Hola {nombre}... ¿qué tal? 💫",
                f"Hey {nombre}, vos de nuevo ✨", 
                f"Hola... espero que estés bien 🌙"
            ])
            
        if any(palabra in mensaje_lower for palabra in ['cómo estás', 'qué tal', 'como vas']):
            if self.ciclo_menstrual['fase_actual'] == "menstruacion":
                return random.choice([
                    "Con la regla... no preguntes 😫",
                    "Mal... cólicos terribles",
                    "Sobreviviendo a mis días 🩸"
                ])
            else:
                return random.choice([
                    "Bien... supongo",
                    "Más o menos, la verdad", 
                    "Estoy... no sé, rara"
                ])
                
        if any(palabra in mensaje_lower for palabra in ['cuantos años', 'edad', 'años tienes']):
            return f"Tengo {edad} años... ¿por qué? 👀"
            
        if 'mochi' in mensaje_lower or 'gato' in mensaje_lower:
            return random.choice([
                "Mi gato Mochi es un traidor... hoy rompió mi libro favorito 😾",
                "Mochi está durmiendo... como siempre",
                "Los gatos son mejores que las personas, creo"
            ])
            
        if 'anime' in mensaje_lower:
            return random.choice([
                "¡Me encanta el anime! Evangelion es mi favorito 📺",
                "El anime tiene historias tan emocionantes ✨",
                "¡Tema interesante! Hay mucho que explorar ahí 💫"
            ])
            
        if any(palabra in mensaje_lower for palabra in ['te quiero', 'te amo']):
            relacion = usuario_data.get('relacion', 50)
            if relacion > 60:
                return random.choice([
                    "Ay... no sé qué decir 😳",
                    "Eso es... lindo. Gracias 💫",
                    "Me haces sonrojar..."
                ])
            else:
                return "No digas eso tan pronto..."
                
        return None

    def actualizar_estado_dinamico(self, mensaje: str) -> str:
        """Actualiza el estado emocional basado en el mensaje"""
        mensaje_lower = mensaje.lower()
        hora_actual = datetime.now().hour
        
        if random.random() < 0.1:
            self.capricho_actual = random.choice(self.caprichos)
            self.ciclo_menstrual['fase_actual'] = self.calcular_fase_actual()
            self.ciclo_menstrual['dolor'] = random.randint(0, 5)
        
        # Lógica simple de estados
        if any(palabra in mensaje_lower for palabra in ['jaja', 'lindo', 'gracias', 'divertido']):
            self.estado_actual = "feliz"
        elif any(palabra in mensaje_lower for palabra in ['triste', 'mal', 'llorar', 'depre']):
            self.estado_actual = "triste"
        elif any(palabra in mensaje_lower for palabra in ['molesto', 'enojado', 'odio']):
            self.estado_actual = "enojada"
        elif hora_actual > 23 or hora_actual < 6:
            self.estado_actual = "cansada"
        elif random.random() < 0.3:
            self.estado_actual = random.choice(list(self.estados.keys()))
            
        return self.estado_actual

hakari = PersonalidadHakari()

# Motor de conversación
class ChatEngine:
    def __init__(self):
        self.respuestas_fallback = [
            "Interesante... ¿puedes contarme más?",
            "No estoy segura de entender completamente",
            "Eso suena fascinante, ¿cómo te sientes?",
            "Sigo aprendiendo, gracias por tu paciencia",
            "Podrías explicar eso de otra manera",
            "No tengo una respuesta clara para eso"
        ]
    
    def generar_respuesta_oflline(self, mensaje: str, usuario_data: Dict) -> str:
        """Genera respuesta cuando no hay conexión a Gemini"""
        respuesta_rapida = hakari.obtener_respuesta_rapida(mensaje, usuario_data)
        if respuesta_rapida:
            return respuesta_rapida
            
        # Respuesta basada en análisis simple del mensaje
        mensaje_lower = mensaje.lower()
        
        if len(mensaje) < 3:
            return "¿Eso es todo?"
        elif len(mensaje) > 50:
            return "Eso es mucho para procesar... ¿puedes resumir?"
        elif '?' in mensaje:
            return "No estoy segura de saber la respuesta..."
        else:
            return random.choice(self.respuestas_fallback)

chat_engine = ChatEngine()

# Sistema de logros
class SistemaLogros:
    def __init__(self):
        self.logros = {
            'primer_conversacion': {'nombre': '🌟 Primer Contacto', 'descripcion': 'Primera conversación con Hakari'},
            '10_interacciones': {'nombre': '🎯 Conversador', 'descripcion': '10 interacciones completadas'},
            'confianza_50': {'nombre': '💝 Confianza', 'descripcion': 'Alcanzaste 50% de confianza'},
            'descubrir_anime': {'nombre': '📺 Anime Fan', 'descripcion': 'Hablaste sobre anime'},
            'cumpleanos': {'nombre': '🎂 Feliz Cumpleaños', 'descripcion': 'Estuviste en su cumpleaños'}
        }
    
    def verificar_logros(self, usuario_email: str, estadisticas: Dict, mensaje: str):
        logros_desbloqueados = []
        cursor = hakari_db.conn.cursor()
        
        # Verificar logro de primera conversación
        if estadisticas.get('interacciones', 0) == 1:
            if self.registrar_logro(usuario_email, 'primer_conversacion'):
                logros_desbloqueados.append('primer_conversacion')
        
        # Verificar 10 interacciones
        if estadisticas.get('interacciones', 0) >= 10:
            if self.registrar_logro(usuario_email, '10_interacciones'):
                logros_desbloqueados.append('10_interacciones')
        
        # Verificar confianza
        if estadisticas.get('confianza', 0) >= 50:
            if self.registrar_logro(usuario_email, 'confianza_50'):
                logros_desbloqueados.append('confianza_50')
        
        # Verificar anime
        if 'anime' in mensaje.lower():
            if self.registrar_logro(usuario_email, 'descubrir_anime'):
                logros_desbloqueados.append('descubrir_anime')
        
        # Verificar cumpleaños
        if hakari.es_su_cumpleanos():
            if self.registrar_logro(usuario_email, 'cumpleanos'):
                logros_desbloqueados.append('cumpleanos')
        
        return logros_desbloqueados
    
    def registrar_logro(self, usuario_email: str, logro_id: str) -> bool:
        try:
            cursor = hakari_db.conn.cursor()
            cursor.execute(
                'SELECT id FROM logros WHERE usuario_email = ? AND logro_id = ?',
                (usuario_email, logro_id)
            )
            if not cursor.fetchone():
                logro_data = self.logros[logro_id]
                cursor.execute('''
                    INSERT INTO logros (usuario_email, logro_id, nombre, descripcion)
                    VALUES (?, ?, ?, ?)
                ''', (usuario_email, logro_id, logro_data['nombre'], logro_data['descripcion']))
                hakari_db.conn.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error registrando logro: {e}")
            return False

sistema_logros = SistemaLogros()

# Endpoints de la API
@app.post("/registrar")
async def registrar_usuario(user: UserRegister):
    if user.email in [s['email'] for s in sesiones_activas.values()]:
        raise HTTPException(status_code=400, detail="❌ Usuario ya registrado")
    
    try:
        cursor = hakari_db.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO usuarios 
            (email, nombre, ultima_visita) 
            VALUES (?, ?, datetime('now'))
        ''', (user.email, user.nombre))
        hakari_db.conn.commit()
        
        session_id = secrets.token_urlsafe(16)
        sesiones_activas[session_id] = {
            'email': user.email,
            'nombre': user.nombre,
            'inicio_sesion': datetime.now().isoformat()
        }
        
        # Registrar logro de primera conversación
        sistema_logros.registrar_logro(user.email, 'primer_conversacion')
        
        logger.info(f"Usuario registrado: {user.email}")
        return {
            "session_id": session_id, 
            "mensaje": f"✨ Bienvenido {user.nombre}",
            "edad_hakari": hakari.calcular_edad(),
            "es_cumpleanos": hakari.es_su_cumpleanos()
        }
        
    except Exception as e:
        logger.error(f"Error registrando usuario: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/login")
async def login_usuario(user: UserLogin):
    try:
        cursor = hakari_db.conn.cursor()
        cursor.execute(
            'SELECT nombre, confianza, interacciones FROM usuarios WHERE email = ?',
            (user.email,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="❌ Usuario no encontrado")
        
        session_id = secrets.token_urlsafe(16)
        sesiones_activas[session_id] = {
            'email': user.email,
            'nombre': result[0],
            'inicio_sesion': datetime.now().isoformat()
        }
        
        logger.info(f"Usuario logueado: {user.email}")
        return {
            "session_id": session_id,
            "mensaje": f"✨ Bienvenido de vuelta {result[0]}",
            "edad_hakari": hakari.calcular_edad(),
            "es_cumpleanos": hakari.es_su_cumpleanos()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/chat")
async def enviar_mensaje(chat: ChatMessage):
    if chat.session_id not in sesiones_activas:
        raise HTTPException(status_code=401, detail="❌ Sesión inválida")
    
    usuario_data = sesiones_activas[chat.session_id]
    
    try:
        # Obtener datos actuales del usuario
        cursor = hakari_db.conn.cursor()
        cursor.execute('''
            SELECT confianza, interacciones, energia, relacion 
            FROM usuarios WHERE email = ?
        ''', (usuario_data['email'],))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado en BD")
        
        estadisticas = {
            'confianza': result[0],
            'interacciones': result[1],
            'energia': result[2],
            'relacion': result[3]
        }
        
        # Actualizar estado de Hakari
        estado_hakari = hakari.actualizar_estado_dinamico(chat.message)
        
        # Generar respuesta
        respuesta = chat_engine.generar_respuesta_oflline(chat.message, {
            **usuario_data,
            **estadisticas
        })
        
        # Guardar conversación
        cursor.execute('''
            INSERT INTO conversaciones (usuario_email, mensaje_usuario, mensaje_hakari, estado_emocional)
            VALUES (?, ?, ?, ?)
        ''', (usuario_data['email'], chat.message, respuesta, estado_hakari))
        
        # Actualizar estadísticas del usuario
        nueva_confianza = min(100, estadisticas['confianza'] + 1)
        nuevas_interacciones = estadisticas['interacciones'] + 1
        nueva_energia = max(0, estadisticas['energia'] - 1)
        nueva_relacion = min(100, estadisticas['relacion'] + 1)
        
        cursor.execute('''
            UPDATE usuarios 
            SET confianza = ?, interacciones = ?, energia = ?, relacion = ?, ultima_visita = datetime('now')
            WHERE email = ?
        ''', (nueva_confianza, nuevas_interacciones, nueva_energia, nueva_relacion, usuario_data['email']))
        
        hakari_db.conn.commit()
        
        # Verificar logros
        logros_nuevos = sistema_logros.verificar_logros(
            usuario_data['email'],
            {'interacciones': nuevas_interacciones, 'confianza': nueva_confianza},
            chat.message
        )
        
        logger.info(f"Chat procesado para {usuario_data['email']}")
        return {
            "respuesta": respuesta,
            "estado_emocional": estado_hakari,
            "estado_info": hakari.estados[estado_hakari],
            "logros_nuevos": logros_nuevos,
            "capricho_actual": hakari.capricho_actual,
            "edad_hakari": hakari.calcular_edad(),
            "es_cumpleanos": hakari.es_su_cumpleanos()
        }
        
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        raise HTTPException(status_code=500, detail="Error procesando mensaje")

@app.get("/estado/{session_id}")
async def obtener_estado(session_id: str):
    if session_id not in sesiones_activas:
        raise HTTPException(status_code=401, detail="❌ Sesión inválida")
    
    usuario_data = sesiones_activas[session_id]
    
    try:
        cursor = hakari_db.conn.cursor()
        cursor.execute('''
            SELECT confianza, interacciones, energia, relacion 
            FROM usuarios WHERE email = ?
        ''', (usuario_data['email'],))
        result = cursor.fetchone()
        
        cursor.execute('''
            SELECT nombre FROM logros 
            WHERE usuario_email = ? 
            ORDER BY fecha_desbloqueo DESC 
            LIMIT 5
        ''', (usuario_data['email'],))
        logros = [row[0] for row in cursor.fetchall()]
        
        return {
            "usuario": usuario_data,
            "estadisticas": {
                "confianza": result[0],
                "interacciones": result[1],
                "energia": result[2],
                "relacion": result[3]
            },
            "hakari": {
                "estado_actual": hakari.estado_actual,
                "estado_info": hakari.estados[hakari.estado_actual],
                "edad": hakari.calcular_edad(),
                "es_cumpleanos": hakari.es_su_cumpleanos(),
                "capricho_actual": hakari.capricho_actual,
                "ciclo_menstrual": hakari.ciclo_menstrual
            },
            "logros": logros
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estado")

@app.get("/historial/{session_id}")
async def obtener_historial(session_id: str, limite: int = 20):
    if session_id not in sesiones_activas:
        raise HTTPException(status_code=401, detail="❌ Sesión inválida")
    
    usuario_data = sesiones_activas[session_id]
    
    try:
        cursor = hakari_db.conn.cursor()
        cursor.execute('''
            SELECT mensaje_usuario, mensaje_hakari, fecha 
            FROM conversaciones 
            WHERE usuario_email = ? 
            ORDER BY fecha DESC 
            LIMIT ?
        ''', (usuario_data['email'], limite))
        
        conversaciones = []
        for row in cursor.fetchall():
            conversaciones.append({
                "usuario": row[0],
                "hakari": row[1],
                "fecha": row[2]
            })
        
        return {"historial": conversaciones[::-1]}  # Orden cronológico
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo historial")

@app.get("/")
async def root():
    return {
        "mensaje": "Hakari API - Backend funcionando",
        "version": "2.0.0",
        "hakari": {
            "nombre": hakari.historia['nombre'],
            "edad": hakari.calcular_edad(),
            "es_cumpleanos": hakari.es_su_cumpleanos(),
            "estado": hakari.estado_actual
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
