# 🎯 Cómo USAR el Dashboard - ¡MUY SIMPLE!

## ✨ La forma MÁS FÁCIL: Haz doble-click

### En Windows
```
Haz doble-click en: start_dashboard.bat
```

¡Eso es todo! Se abrirá automáticamente en tu navegador.

---

### En Mac/Linux
```bash
chmod +x start_dashboard.sh
./start_dashboard.sh
```

---

## 🌐 Si prefieres hacerlo manual

### Paso 1: Abre tu terminal/PowerShell en esta carpeta

```bash
cd C:\Users\anama\Downloads\Github\job-search-automation
```

### Paso 2: Ejecuta el servidor

```bash
# Opción A: Con el script
start_dashboard.bat    # Windows
./start_dashboard.sh   # Mac/Linux

# Opción B: Manual
source venv/Scripts/activate  # Windows Bash
.\venv\Scripts\activate.ps1   # Windows PowerShell
source venv/bin/activate      # Mac/Linux

python -m web.app
```

### Paso 3: Abre en navegador

```
http://localhost:8000
```

---

## 👀 Qué verás

**Una página bonita con:**

```
┌─ BÚSQUEDA RÁPIDA (1 página) ─┐
├─ BÚSQUEDA NORMAL (3 páginas) ─┤
├─ BÚSQUEDA PROFUNDA (5 páginas)┤
└─ SOLO REMOTO (checkbox)       ─┘

┌─ ESTADÍSTICAS ─┐
├─ Total: 45     ├─ Remoto: 40
├─ Computrabajo: 25 ├─ Bumerán: 20
└─────────────────┘

┌─ LISTA DE OFERTAS ─┐
├─ React Junior Developer       ├─ Remoto ├─ $2000-3000 ├─ Ver oferta
├─ Frontend Engineer            ├─ Remoto ├─ $2500-4000 ├─ Ver oferta
├─ Node.js Developer            ├─ Remoto ├─ $2200-3500 ├─ Ver oferta
└────────────────────────────────────────────────────────┘
```

---

## 🎮 Qué hacer en el Dashboard

### 1. **BUSCAR OFERTAS**
   - Click en "Búsqueda rápida" (1-2 minutos)
   - O "Búsqueda normal" si tienes tiempo (2-3 minutos)
   - Espera a que cargue (verás una barra de progreso)

### 2. **VER OFERTAS**
   - Se actualizan automáticamente
   - Muestra: Título, Empresa, Ubicación, Salario, Fuente

### 3. **APLICAR**
   - Click en "Ver oferta →"
   - Se abre en Computrabajo/Bumerán directamente
   - Postúlate como de costumbre

### 4. **VER ESTADÍSTICAS**
   - En la parte superior (tarjetas de números)
   - Total de ofertas, cuántas son remoto, por fuente

### 5. **FILTROS**
   - Checkbox "Solo remoto" (está checkeado por defecto)
   - Desmarca si quieres ver no-remoto también

---

## ⏱️ Tiempo típico

```
Buscar ofertas: 2-3 minutos
Ver ofertas: 30 segundos
Aplicar a una: 5 minutos (en el sitio de la empresa)

Total por día: 30 minutos si aplicas a 5-10 ofertas
```

---

## 🆘 Si algo no funciona

### "Conexión rechazada" o "No se puede conectar"
```bash
# Asegúrate de que:
1. Abriste correctamente start_dashboard.bat/.sh
2. Esperaste 5 segundos
3. Abriste http://localhost:8000 (NO https)

# Si aún no funciona:
python -m web.app
# Verás: "Uvicorn running on http://0.0.0.0:8000"
```

### "Puerto 8000 en uso"
```bash
# Cierra otras apps usando ese puerto
# O usa otro:
python -m uvicorn web.app:app --port 8001
# Luego abre: http://localhost:8001
```

### No carga las ofertas
```bash
1. Click en "Búsqueda rápida"
2. Espera 2-3 minutos
3. Las ofertas aparecerán
```

---

## 📱 En tu celular/tablet

Si quieres usar desde otro dispositivo:

```bash
# En tu PC, ejecuta el dashboard
# Obtén tu IP: ipconfig (Windows)

# Desde tu celular abre:
http://192.168.1.100:8000
# (reemplaza con tu IP real)
```

---

## 🎯 Uso diario (5 minutos)

```bash
1. Double-click en start_dashboard.bat (o .sh)
2. Espera a que se abra el navegador
3. Click en "Búsqueda rápida"
4. Espera 2 minutos
5. Click en las ofertas que te interesen
6. Cierra cuando termines (Ctrl+C)
```

**¡Eso es todo!**

---

## 💡 Tips

✅ Ejecuta 2-3 veces al día para nuevas ofertas  
✅ Las ofertas se guardan automáticamente  
✅ No necesitas usar la línea de comandos  
✅ El dashboard se actualiza cada 30 segundos  
✅ Puedes tener el dashboard abierto todo el día  

---

## 🚀 Eso es todo

No hay nada más complicado. Es:

1. **Double-click** → Abre el dashboard
2. **Click buscar** → Encuentra ofertas
3. **Click ver** → Abre en el sitio
4. **Postúlate** → Como siempre

**¡Simple! ✨**

---

**¿Dudas?** Lee `WEB_DASHBOARD.md` para más detalles.

**¿Problemas?** Verifica que tengas `FastAPI` instalado:
```bash
pip install fastapi uvicorn
```

**¡Éxito en tu búsqueda!** 💼
