# Configuración Inicial - Job Search Automation

## Paso 1: Identificar tu país/región

Este proyecto funciona en múltiples países de Latinoamérica. Identifica cuál es el tuyo:

- **Colombia**: computrabajo.com.co, bumeran.com.co
- **Argentina**: computrabajo.com.ar, bumeran.com.ar
- **México**: computrabajo.com.mx, bumeran.com.mx
- **Chile**: computrabajo.cl, bumeran.cl
- **Perú**: computrabajo.com.pe, bumeran.pe
- **Otros**: Usa el URL base de tu país

## Paso 2: Configurar URLs correctos

Abre el archivo `config/settings.py` y actualiza:

```python
COMPUTRABAJO_BASE_URL = "https://www.computrabajo.com.co"  # Cambia a tu país
BUMERAN_BASE_URL = "https://www.bumeran.com.co"           # Cambia a tu país
```

## Paso 3: Configurar palabras clave

Edita `.env` y personaliza `KEYWORDS`:

```env
# Para Frontend Developer
KEYWORDS=react,frontend,javascript,vue,angular,html,css,node.js,junior,trainee

# Para Data Analyst
KEYWORDS=data analyst,python,sql,powerbi,excel,analisis de datos,junior

# Para Full-stack
KEYWORDS=full-stack,react,node.js,python,javascript,frontend,backend
```

## Paso 4: Ejecutar por primera vez

```bash
# Activar virtual environment
source venv/Scripts/activate  # Windows
source venv/bin/activate      # macOS/Linux

# Inicializar base de datos
python run.py init

# Buscar ofertas (comenzar con pocas páginas)
python run.py scrape --pages 1

# Ver qué encontró
python run.py list

# Ver estadísticas
python run.py stats
```

## Troubleshooting

### Si no encuentra ofertas

1. **Verifica los URLs**: Asegúrate de usar los correctos para tu país
   ```bash
   # Prueba manualmente en navegador
   https://www.computrabajo.com.co/bt_react/p_1
   https://www.bumeran.com.co/empleos-buscar-react-pagina-1.html
   ```

2. **Aumenta páginas**: Los primeros scrapes pueden no encontrar nada
   ```bash
   python run.py scrape --pages 5
   ```

3. **Usa Apify** (opción premium, más confiable):
   - Crea cuenta en https://apify.com
   - Obtén tu API key
   - Agrega a `.env`: `APIFY_API_KEY=tu_clave_aqui`

4. **Revisa keywords**: Asegúrate de que sean relevantes
   ```bash
   python run.py list --limit 50  # Ver todas las ofertas guardadas
   ```

### Si recibe errores de conexión

- Algunos portales tienen protecciones anti-bot
- Espera más entre scrapes (reduce frecuencia)
- Intenta con menos páginas al principio
- Considera usar Apify como alternativa

## Próximos pasos

1. Ejecuta scrapes regularmente (2-3 veces al día)
2. Revisa las ofertas filtradas
3. Agrega tus propias reglas de filtrado en `filters/job_filter.py`
4. Crea un archivo de tracking para monitorear postulaciones

## Ayuda

Para más información:
- Lee el `README.md` para comandos disponibles
- Revisa `config/settings.py` para todas las opciones
- Abre un issue si encuentras problemas
