# QuickStart - Comienza en 5 minutos

## 1️⃣ Activar el entorno virtual

**Windows:**
```bash
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

## 2️⃣ Inicializar la base de datos (primera vez)

```bash
python run.py init
```

Esto crea el archivo `jobs.db` con las tablas necesarias.

## 3️⃣ Buscar ofertas de empleo

```bash
# Búsqueda rápida (primera página)
python run.py scrape --pages 1

# Búsqueda más profunda (5 páginas)
python run.py scrape --pages 5

# Búsqueda estándar (3 páginas)
python run.py scrape
```

⏱️ **Tiempo estimado:** 1-3 minutos

## 4️⃣ Ver resultados

```bash
# Ver las mejores 20 ofertas
python run.py list

# Ver 50 ofertas
python run.py list --limit 50

# Ver también ofertas no-remoto
python run.py list --all-locations
```

## 5️⃣ Ver estadísticas

```bash
python run.py stats
```

Muestra:
- Total de ofertas guardadas
- Cuántas son remoto
- Ofertas por portal (Computrabajo, Bumerán)

---

## Uso diario recomendado

```bash
# Cada mañana (5 minutos)
source venv/bin/activate      # Activar
python run.py scrape          # Buscar nuevas ofertas
python run.py list --limit 10 # Ver top 10
```

Luego abre los links en tu navegador y postula directamente.

---

## 🎯 Comandos disponibles

| Comando | Descripción |
|---------|-----------|
| `python run.py init` | Inicializar base de datos |
| `python run.py scrape` | Buscar ofertas (3 páginas por defecto) |
| `python run.py scrape --pages N` | Buscar N páginas |
| `python run.py list` | Ver 20 ofertas filtradas |
| `python run.py list --limit N` | Ver N ofertas |
| `python run.py list --all-locations` | Incluir no-remoto |
| `python run.py stats` | Ver estadísticas |
| `python run.py clear` | Limpiar base de datos |

---

## ⚙️ Personalización

### Cambiar palabras clave

Edita `.env`:
```env
KEYWORDS=react,nodejs,python,data analyst,junior
```

### Cambiar a otro país

Ejecuta el wizard nuevamente:
```bash
python config_wizard.py
```

O edita manualmente `config/settings.py`:
```python
COMPUTRABAJO_BASE_URL = "https://www.computrabajo.com.ar"  # Argentina
BUMERAN_BASE_URL = "https://www.bumeran.com.ar"
```

### Incluir ofertas no-remoto

Edita `.env`:
```env
REMOTE_ONLY=false
```

---

## ❓ Troubleshooting

**P: No encuentra ofertas**  
R: Intenta con más páginas: `python run.py scrape --pages 5`

**P: Recibe errores de conexión**  
R: El sitio tiene protecciones anti-bot. Espera unos minutos e intenta de nuevo.

**P: ¿Es legal hacer scraping?**  
R: Sí, el scraping de Computrabajo y Bumerán es legal. LinkedIn es más restrictivo.

---

## 🚀 Próximos pasos

1. ✅ **Ahora:** Usa el sistema para buscar ofertas
2. ⏳ **Próxima fase:** Integración con LinkedIn
3. ⏳ **Después:** Dashboard web y asistente de postulaciones
4. ⏳ **Final:** Portafolio profesional integrado

---

## 📞 Necesitas ayuda?

- Lee `README.md` para más comandos
- Lee `SETUP.md` para configuración avanzada
- Lee `PROJECT_SUMMARY.md` para entender toda la arquitectura

¡Éxito en tu búsqueda de trabajo! 💪
