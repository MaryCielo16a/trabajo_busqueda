# 🌐 Dashboard Web - Job Search Automation

Tu sistema ahora tiene una **interfaz web bonita** en lugar de línea de comandos.

## ✨ Características del Dashboard

✅ **Búsqueda visual** - Con un click
✅ **Ver ofertas en tabla** - Limpia y organizada
✅ **Estadísticas en tiempo real** - Total, remoto, por portal
✅ **Barra de progreso** - Ver el avance del scraping
✅ **Sin línea de comandos** - Todo en el navegador
✅ **Filtros** - Solo remoto, por fuente, por palabras clave
✅ **Links directos** - Abre ofertas en nueva pestaña

---

## 🚀 Ejecutar el Dashboard

### 1️⃣ Actualizar dependencias

```bash
pip install -r requirements.txt
```

### 2️⃣ Activar virtual environment

**Windows:**
```bash
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3️⃣ Iniciar el servidor

```bash
python -m web.app
```

O también:
```bash
python web/app.py
```

Verás algo como:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4️⃣ Abrir en navegador

**Simplemente abre:** http://localhost:8000

¡Listo! Ya tienes tu dashboard corriendo.

---

## 📋 Qué puedes hacer

### 🔍 Búsqueda rápida (1 página)
- ⚡ 1-2 minutos
- Ideal para búsquedas frecuentes

### 🔎 Búsqueda normal (3 páginas)
- ⏱️ 2-3 minutos
- Recomendado al empezar

### 🔎🔎 Búsqueda profunda (5 páginas)
- ⏰ 5-10 minutos
- Para análisis exhaustivo

### 📊 Estadísticas
- Ver total de ofertas guardadas
- Cuántas son remoto
- Ofertas por portal (Computrabajo, Bumerán)

### 💾 Limpiar BD
- Borrar todas las ofertas guardadas
- Empezar de cero

---

## 🎨 Interfaz

El dashboard muestra:

**Arriba:**
- Título y descripción
- Botones de búsqueda (rápida, normal, profunda)
- Checkbox "Solo remoto"

**Tarjetas de estadísticas:**
- Total de ofertas
- Ofertas remoto
- Ofertas por fuente

**Lista de ofertas:**
- Título de la oferta
- Empresa
- Ubicación (remoto/ciudad)
- Salario (si está disponible)
- Fuente (Computrabajo, Bumerán)
- Botón para ver oferta en Computrabajo/Bumerán

---

## ⚙️ Configuración

El dashboard usa la misma configuración que la CLI:
- `.env` - Keywords, solo remoto, etc.
- `config/settings.py` - URLs, headers, etc.

**Para cambiar país/rol:**
```bash
python config_wizard.py
```

Luego reinicia el servidor (Ctrl+C y vuelve a ejecutar).

---

## 🔧 Troubleshooting

### Puerto 8000 ya está en uso
```bash
# Usar otro puerto
python -m uvicorn web.app:app --port 8001

# Luego abre: http://localhost:8001
```

### Error: "No module named fastapi"
```bash
pip install -r requirements.txt
```

### El dashboard se ve extraño
- Limpia caché del navegador (Ctrl+Shift+Delete)
- Recarga la página (Ctrl+F5 o Cmd+Shift+R)

### No carga ofertas
- Asegúrate de haber hecho un scrape antes
- Click en "Búsqueda rápida"
- Espera 2-3 minutos

---

## 📱 Acceso desde otros dispositivos

Si quieres acceder desde otro dispositivo en tu red:

1. Encuentra tu IP local: `ipconfig` (Windows) o `ifconfig` (Mac/Linux)
2. Accede desde otro dispositivo: `http://TU_IP:8000`

Ejemplo:
```bash
# En tu PC
python -m web.app

# En tu celular/tablet, abre:
http://192.168.1.100:8000
```

---

## 🎯 Uso diario recomendado

```bash
# Cada mañana
.\venv\Scripts\activate
python -m web.app

# Abre http://localhost:8000 en tu navegador
# Click en "Búsqueda rápida"
# Revisa las ofertas
# Clickea en las que te interesan
```

Eso es todo. Muy simple.

---

## 🚀 Próximas mejoras

- [ ] Notificaciones por email
- [ ] Integración LinkedIn
- [ ] Guardar ofertas favoritas
- [ ] Historial de postulaciones
- [ ] Estadísticas avanzadas
- [ ] Exportar a Excel

---

## 📝 Detección automática

El dashboard se actualiza automáticamente cada 30 segundos. Si haces un scraping en otra terminal, verá los nuevos cambios.

**Ejemplo:**
```bash
# Terminal 1
python -m web.app

# Terminal 2 (en la misma carpeta, mismo venv)
python run.py scrape

# El dashboard se actualizará automáticamente
```

---

## 💡 Tips

1. **Maximiza la ventana** - El dashboard es responsivo
2. **Usa "Solo remoto"** - Checkbox en los controles
3. **Ejecuta búsquedas regularmente** - 2-3 veces al día
4. **Abre ofertas en nueva pestaña** - Click derecho + "Abrir en nueva pestaña"

---

## ✅ Checklist

- [ ] Instalé las dependencias: `pip install -r requirements.txt`
- [ ] Activé el venv: `.\venv\Scripts\activate`
- [ ] Ejecuté: `python -m web.app`
- [ ] Abrí: `http://localhost:8000`
- [ ] Hice una búsqueda rápida
- [ ] Vi las ofertas

¡Si todo funciona, ¡felicidades! 🎉

---

**Versión:** 1.0 Dashboard Web  
**Última actualización:** Agosto 2026  
**Status:** ✅ Funcional
