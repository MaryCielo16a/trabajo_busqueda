# 🎉 ¡Bienvenido a Job Search Automation!

Tu sistema de búsqueda automática de trabajo está **completamente configurado y listo para usar**.

## ✅ Lo que ya está hecho

- ✅ Sistema de scraping para Computrabajo y Bumerán
- ✅ Base de datos SQLite para guardar ofertas
- ✅ Filtrado inteligente por palabras clave y ubicación
- ✅ Interfaz CLI fácil de usar
- ✅ Configuración optimizada para Colombia, Frontend Developer, 100% remoto
- ✅ Toda la documentación

## 🚀 Comienza AHORA (3 pasos)

### Paso 1: Abre una terminal en esta carpeta

```bash
# En Windows PowerShell o CMD
cd C:\Users\anama\Downloads\Github\job-search-automation

# O en Git Bash
cd ~/Downloads/Github/job-search-automation
```

### Paso 2: Activa el entorno virtual

```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (CMD)
.\venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

### Paso 3: ¡Busca ofertas!

```bash
# Ver ofertas guardadas previamente
python run.py list

# O buscar nuevas ofertas (1-2 minutos)
python run.py scrape --pages 1
python run.py list
```

**¡Listo!** Ya tienes una lista de ofertas de trabajo remoto en frontend.

---

## 📖 Documentación rápida

Dependiendo de lo que necesites:

| Necesito | Leer |
|----------|------|
| **Empezar rápido** (5 min) | [`QUICKSTART.md`](QUICKSTART.md) |
| **Todos los comandos** | [`README.md`](README.md) |
| **Configurar otro país** | [`SETUP.md`](SETUP.md) |
| **Entender la arquitectura** | [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) |
| **Estructura de archivos** | [`FILES.md`](FILES.md) |

---

## 💡 Uso diario recomendado (5 minutos)

```bash
# Cada mañana
source venv/Scripts/activate     # Activar (si no está activo)
python run.py scrape            # Buscar nuevas ofertas
python run.py list --limit 10   # Ver las 10 mejores

# Luego abre los links en tu navegador y postula
```

Eso es todo. El sistema mantiene un registro de todas las ofertas encontradas.

---

## 🎯 Comandos principales

```bash
# 📊 Ver estadísticas
python run.py stats

# 💼 Ver todas las ofertas
python run.py list --limit 50

# 🔍 Buscar nuevas (1 página = rápido)
python run.py scrape --pages 1

# 🔍 Buscar más (5 páginas = exhaustivo)
python run.py scrape --pages 5

# 🗑️ Limpiar base de datos (si quieres empezar de nuevo)
python run.py clear
```

---

## 📋 Tu configuración actual

**País:** Colombia  
**Rol objetivo:** Frontend Developer  
**Ubicación:** Solo remoto  
**Tecnologías:** React, Vue, Angular, JavaScript, Node.js, etc.  

¿Quieres cambiar? Ejecuta: `python config_wizard.py`

---

## ⚠️ Cosas importantes a saber

### ✅ Es legal
El web scraping de Computrabajo y Bumerán está permitido y es una práctica común.

### ⏱️ Timing
- Primer scrape: 2-3 minutos
- Scrapes posteriores: 1-2 minutos
- No hagas scrapes más de cada 30 minutos (evita bloqueos)

### 🔄 Actualizaciones
- Ejecuta `scrape` 2-3 veces al día para nuevas ofertas
- Las ofertas antiguas se guardan automáticamente

### 💾 Backup
- Tu base de datos se guarda en `jobs.db`
- Haz backup regularmente: `cp jobs.db jobs.db.backup`

---

## 🆘 Si algo no funciona

### No encuentra ofertas
```bash
# Intenta buscar más páginas
python run.py scrape --pages 5

# Verifica estadísticas
python run.py stats

# Intenta de nuevo en 5 minutos
```

### Errores de conexión
Algunos portales tienen anti-bot. Espera un rato e intenta de nuevo.

### Error: "ModuleNotFoundError"
```bash
# Reinstala dependencias
pip install -r requirements.txt

# Y luego intenta de nuevo
python run.py list
```

### ¿Más ayuda?
- Lee [`SETUP.md`](SETUP.md) para troubleshooting completo
- Verifica que estés en la carpeta correcta: `pwd`
- Verifica que virtual env esté activo: `python --version` (debe ser Python 3.10+)

---

## 🔜 Próximas fases (en desarrollo)

**Fase 2:** Integración con LinkedIn  
**Fase 3:** Portafolio web profesional  
**Fase 4:** Asistente de postulaciones automático  
**Fase 5:** Dashboard y analytics  

---

## 📞 ¿Necesitas ayuda configurando otro país?

Si no eres de Colombia:

```bash
# Ejecuta el asistente
python config_wizard.py

# Selecciona:
# - Tu país
# - Tu rol objetivo (Frontend, Backend, Full-stack, Data Analyst)
# - Tus preferencias
```

Soportamos: Colombia, Argentina, México, Chile, Perú y muchos más.

---

## 🎓 ¿Quieres aprender cómo funciona?

Revisa [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) para:
- Arquitectura del proyecto
- Cómo funcionan los scrapers
- Cómo personalizar filtros
- Tecnologías utilizadas

---

## 🏁 Resumen

| Tarea | Comando | Tiempo |
|-------|---------|--------|
| Ver ofertas guardadas | `python run.py list` | 10 seg |
| Buscar nuevas ofertas | `python run.py scrape` | 2-3 min |
| Ver estadísticas | `python run.py stats` | 10 seg |
| Reconfigurar país/rol | `python config_wizard.py` | 1 min |

---

## 🚀 ¡Listo para empezar?

```bash
# Copia y pega esto en tu terminal:
source venv/Scripts/activate && python run.py scrape --pages 1 && python run.py list
```

**¡Éxito en tu búsqueda de trabajo!** 💼✨

---

**Proyecto creado:** Agosto 2026  
**Versión:** 1.0  
**Status:** ✅ Fase 1 completada  
**Próxima:** Fase 2 (LinkedIn + notificaciones)
