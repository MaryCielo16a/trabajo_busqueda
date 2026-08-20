# Estructura de archivos - Job Search Automation

## 📁 Carpetas principales

### `/cli/` - Interfaz de línea de comandos
- `__init__.py` - Marca como paquete Python
- `main.py` - CLI principal con todos los comandos

### `/config/` - Configuración centralizada
- `__init__.py` - Marca como paquete Python
- `settings.py` - Variables de configuración (URLs, keywords, etc.)

### `/database/` - Modelos y acceso a datos
- `__init__.py` - Marca como paquete Python
- `models.py` - Modelos SQLAlchemy (Job, Application, UserPreferences)

### `/scrapers/` - Web scrapers
- `__init__.py` - Marca como paquete Python
- `computrabajo_scraper.py` - Scraper para Computrabajo
- `bumeran_scraper.py` - Scraper para Bumerán
- `apify_scraper.py` - Integración con Apify (premium, opcional)

### `/filters/` - Lógica de filtrado
- `__init__.py` - Marca como paquete Python
- `job_filter.py` - Filtro inteligente de ofertas

### `/logs/` - Logs de scraping (generada automáticamente)
- Vacía inicialmente, se llena con logs cuando ejecutas scrapes

## 📄 Archivos de configuración

### Configuración del proyecto
- `.env` - Tu configuración personalizada (generado por `config_wizard.py`)
- `.env.example` - Plantilla de ejemplo
- `requirements.txt` - Dependencias Python
- `.gitignore` - Archivos a ignorar en Git
- `config_wizard.py` - Asistente interactivo de configuración

## 🚀 Punto de entrada

- `run.py` - Script principal (usa esto para ejecutar comandos)

## 📚 Documentación

### Guías de uso
- `QUICKSTART.md` ⭐ **EMPIEZA AQUÍ** - Guía de 5 minutos
- `README.md` - Guía completa con todos los comandos
- `SETUP.md` - Guía de configuración avanzada
- `FILES.md` - Este archivo (estructura del proyecto)

### Documentación del proyecto
- `PROJECT_SUMMARY.md` - Resumen ejecutivo, arquitectura, próximas fases
- `plan.md` - Plan original aprobado

## 💾 Base de datos (generada automáticamente)

- `jobs.db` - SQLite database
  - Tabla `jobs` - Ofertas encontradas
  - Tabla `applications` - Historial de postulaciones
  - Tabla `user_preferences` - Preferencias guardadas

## 📦 Virtual environment (no subir a Git)

- `venv/` - Entorno virtual Python
  - No incluir en Git (ya en `.gitignore`)
  - Recrear con: `pip install -r requirements.txt`

## 🔍 Cómo navegar por el código

### Para entender qué hace cada parte:

1. **Empezar por:** `run.py` → `cli/main.py`
   - Entiende los comandos disponibles

2. **Luego:** `config/settings.py`
   - Ve la configuración centralizada

3. **Scrapers:** `scrapers/computrabajo_scraper.py` y `scrapers/bumeran_scraper.py`
   - Entiende cómo se extraen datos

4. **Base de datos:** `database/models.py`
   - Entiende la estructura de datos

5. **Filtros:** `filters/job_filter.py`
   - Entiende cómo se filtran ofertas

### Diagrama de dependencias:

```
run.py (punto de entrada)
  ↓
cli/main.py (comandos)
  ├── scrapers/ (obtienen datos)
  │   ├── computrabajo_scraper.py
  │   ├── bumeran_scraper.py
  │   └── apify_scraper.py
  ├── database/models.py (guardan datos)
  ├── filters/job_filter.py (filtran datos)
  └── config/settings.py (configuración)
```

## 📝 Archivos importantes a no olvidar

| Archivo | Importancia | Acción si se daña |
|---------|-----------|------------------|
| `.env` | ⭐⭐⭐ | Regenerar con `python config_wizard.py` |
| `jobs.db` | ⭐⭐ | Regenerar con `python run.py clear` |
| `config/settings.py` | ⭐⭐ | Regenerar con `python config_wizard.py` |
| `scrapers/*.py` | ⭐⭐⭐ | Recuperar de Git |
| `cli/main.py` | ⭐⭐⭐ | Recuperar de Git |
| `requirements.txt` | ⭐⭐ | Reinstalar: `pip install -r requirements.txt` |

## 🔄 Próximos archivos (Fase 2+)

Cuando continúes con las próximas fases, se agregarán:

```
job-search-automation/
├── /services/          # Servicios de notificación
│   ├── email_service.py
│   └── telegram_service.py
├── /web/               # Dashboard web (Fase 4)
│   ├── app.py          # FastAPI backend
│   └── static/         # Frontend React
├── /scripts/           # Scripts auxiliares
│   ├── scheduler.py    # Ejecutar scrapes automáticamente
│   └── backup.py       # Backup de base de datos
├── /tests/             # Tests unitarios
│   ├── test_scrapers.py
│   └── test_filters.py
└── docker-compose.yml  # Deployment
```

---

**Última actualización:** Agosto 2026  
**Versión:** 1.0 (Fase 1 completada)
