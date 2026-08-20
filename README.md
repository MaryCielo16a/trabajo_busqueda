# Job Search Automation 🚀

Automatiza tu búsqueda de trabajo en LinkedIn, Computrabajo y Bumerán. Filtra ofertas por tus criterios y encuentra tu próximo empleo como Ingeniero de Sistemas.

## Características

✅ **Búsqueda automática** en Computrabajo y Bumerán  
✅ **Filtrado inteligente** por ubicación, stack y experiencia  
✅ **Base de datos local** para tracking de ofertas  
✅ **CLI simple** para usar desde terminal  
✅ **Configuración flexible** vía variables de entorno  

## Instalación

### 1. Clonar repositorio y entrar en la carpeta
```bash
cd job-search-automation
```

### 2. Activar el virtual environment

**En Windows:**
```bash
.\venv\Scripts\activate
```

**En macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

**Opción A: Configuración interactiva (recomendado)**
```bash
python config_wizard.py
```
Este wizard te guiará paso a paso para configurar:
- País/región
- Rol objetivo (Frontend, Backend, Full-stack, Data Analyst)
- Preferencias de búsqueda (remoto, ubicación)
- API keys opcionales (Apify)

**Opción B: Configuración manual**
Copia el archivo `.env.example` a `.env`:
```bash
cp .env.example .env
```

Luego edita `.env` con tus preferencias:
```env
REMOTE_ONLY=true
KEYWORDS=react,frontend,javascript,python,fullstack,data analyst
```

Para más detalles de configuración, ver `SETUP.md`

### 5. Inicializar base de datos
```bash
python cli/main.py init
```

## Uso

### Buscar y guardar ofertas
```bash
python cli/main.py scrape
```

Opciones:
- `--pages 5` - Buscar en 5 páginas en lugar de 3 (defecto)
- Ejemplo: `python cli/main.py scrape --pages 5`

### Ver ofertas filtradas
```bash
python cli/main.py list
```

Opciones:
- `--limit 50` - Mostrar hasta 50 ofertas (defecto: 20)
- `--all-locations` - Incluir ofertas no-remoto
- Ejemplo: `python cli/main.py list --limit 30`

### Ver estadísticas
```bash
python cli/main.py stats
```

Muestra:
- Total de ofertas en base de datos
- Cantidad de ofertas remoto
- Ofertas por fuente (Computrabajo, Bumerán)

### Limpiar base de datos
```bash
python cli/main.py clear
```

## Flujo de uso recomendado

### Primera vez (Setup inicial)
```bash
# 1. Inicializar base de datos
python cli/main.py init

# 2. Buscar ofertas por primera vez
python cli/main.py scrape --pages 5

# 3. Ver qué encontró
python cli/main.py list

# 4. Ver estadísticas
python cli/main.py stats
```

### Uso diario
```bash
# Ejecutar cada mañana para buscar nuevas ofertas
python cli/main.py scrape

# Ver las mejores ofertas
python cli/main.py list
```

## Personalización

### Cambiar palabras clave de búsqueda

Edita el archivo `.env`:
```env
KEYWORDS=tu-tecnologia-1,tu-tecnologia-2,rol-deseado
```

Ejemplo para data scientist:
```env
KEYWORDS=data analyst,python,sql,analisis de datos,estadistica,machine learning
```

### Buscar solo ubicaciones específicas

Modifica `filters/job_filter.py` para agregar filtros de ubicación.

### Cambiar frecuencia de búsqueda

Edita `.env`:
```env
SCRAPE_INTERVAL_MINUTES=120  # Buscar cada 2 horas
```

## Estructura del proyecto

```
job-search-automation/
├── cli/
│   ├── main.py          # CLI principal
│   └── __init__.py
├── scrapers/
│   ├── computrabajo_scraper.py   # Scraper para Computrabajo
│   ├── bumeran_scraper.py        # Scraper para Bumerán
│   └── __init__.py
├── database/
│   ├── models.py        # Modelos SQLAlchemy
│   └── __init__.py
├── filters/
│   ├── job_filter.py    # Lógica de filtrado
│   └── __init__.py
├── config/
│   ├── settings.py      # Configuración
│   └── __init__.py
├── requirements.txt     # Dependencias Python
├── .env.example         # Ejemplo de configuración
└── jobs.db              # Base de datos SQLite (generada)
```

## Próximos pasos (Fase 2)

- [ ] Integración con LinkedIn (Selenium)
- [ ] Generador automático de cover letters
- [ ] Dashboard web con visualización de ofertas
- [ ] Sistema de notificaciones por email
- [ ] Tracker de postulaciones

## Notas importantes

**Legalidad:**
- El scraping de Computrabajo y Bumerán es técnicamente viable
- Revisa los Términos de Servicio de cada plataforma
- No automatices postulaciones completas (violaría ToS)

**Performance:**
- Los primeros scrapes pueden tardar 2-5 minutos
- No hagas scrapes más frecuente que cada 30 minutos para evitar bloqueos
- Usa `--pages` limitado (3-5) para búsquedas rápidas

## Troubleshooting

### "ModuleNotFoundError: No module named 'beautifulsoup4'"
Asegúrate de activar el virtual environment y haber instalado dependencias:
```bash
pip install -r requirements.txt
```

### Los scrapers no encuentran nada
- Verifica que los URLs de Computrabajo/Bumerán sean correctos
- Intenta aumentar el número de páginas: `python cli/main.py scrape --pages 5`
- Revisa los keywords en `.env`

### Bloqueo de IP (Too many requests)
- Reduce la frecuencia de scrapes (espera más entre búsquedas)
- Intenta usar el cliente de Apify como alternativa (Fase 2)

## Licencia

MIT License - Úsalo como quieras 😊

---

**¿Preguntas o sugerencias?** Abre un issue o contacta a través de tu email.
