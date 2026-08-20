# 🚀 Deployment a Internet - GRATIS

Tu sistema Job Search Automation en la nube, accesible desde cualquier lado.

**Tiempo total:** 10-15 minutos  
**Costo:** $0 (planes gratuitos)

---

## 📋 Lo que necesitas

1. Cuenta GitHub (gratuita)
2. Cuenta Railway (gratuita)
3. Cuenta Vercel (gratuita)

---

## PASO 1️⃣: Subir código a GitHub

### 1. Crear repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre: `job-search-automation`
3. Descripción: "Sistema automático de búsqueda de trabajo"
4. **Selecciona: Public** (para que Railway pueda verlo)
5. Click: "Create repository"

### 2. Subir tu código

En tu terminal:

```bash
cd C:\Users\anama\Downloads\Github\job-search-automation

# Inicializar git
git init
git add .
git commit -m "Initial commit: Job Search Automation"

# Cambiar nombre de rama (si es necesario)
git branch -M main

# Agregar remote (reemplaza TU_USUARIO)
git remote add origin https://github.com/TU_USUARIO/job-search-automation.git

# Subir código
git push -u origin main
```

**Nota:** Usa tu usuario de GitHub en lugar de `TU_USUARIO`

---

## PASO 2️⃣: Desplegar Backend en Railway

### 1. Ir a Railway

https://railway.app

### 2. Conectar GitHub

1. Click: "Start a New Project"
2. Click: "Deploy from GitHub repo"
3. Autoriza Railway con tu GitHub
4. Selecciona: `job-search-automation`
5. Click: "Deploy"

### 3. Esperar deployment

Railway automáticamente:
- Lee el `Procfile`
- Instala dependencias
- Inicia el servidor

⏱️ Espera 2-3 minutos...

### 4. Obtener URL pública

Cuando termine:
1. Click en el proyecto
2. Click en "Deployments"
3. Abre "Service"
4. En "Settings" → "Domain"
5. Verás algo como: `https://job-search-automation-production.up.railway.app`

**⚠️ COPIA ESTA URL** - La necesitarás para el frontend

---

## PASO 3️⃣: Actualizar Frontend

Tu frontend HTML necesita conocer la URL del backend en Railway.

### 1. Editar `web/static/index.html`

Busca estas líneas (al inicio del `<script>`):

```javascript
// Cambiar de:
const API_URL = 'http://localhost:8000';

// A:
const API_URL = 'https://tu-url-de-railway.app';
```

Reemplaza `https://tu-url-de-railway.app` con tu URL real de Railway.

### 2. Actualizar todos los `fetch()`

En el archivo HTML, busca todos los `fetch(` y reemplaza:

```javascript
// Antes:
const response = await fetch(`/api/jobs?limit=50`);

// Después:
const response = await fetch(`${API_URL}/api/jobs?limit=50`);
```

**Más fácil:** Busca y reemplaza:
- `fetch('/api/` → `fetch('${API_URL}/api/`
- `fetch('http://localhost` → `fetch('${API_URL}`

### 3. Commit y push

```bash
git add .
git commit -m "Update API URL for production"
git push
```

---

## PASO 4️⃣: Desplegar Frontend en Vercel

### 1. Ir a Vercel

https://vercel.com

### 2. Conectar GitHub

1. Click: "New Project"
2. Click: "Import from GitHub"
3. Selecciona: `job-search-automation`
4. Click: "Import"

### 3. Configurar

En "Configure project":
- **Framework Preset:** Other
- No necesitas hacer nada más

Click: "Deploy"

⏱️ Espera 1-2 minutos...

### 4. Obtener URL pública

Cuando termine:
- Verás: "Congratulations"
- Algo como: `https://job-search-automation.vercel.app`

**LISTO! 🎉**

---

## ✅ Verificar que funciona

Abre en tu navegador:
```
https://job-search-automation.vercel.app
```

Deberías ver:
- ✅ Dashboard bonito
- ✅ Botones de búsqueda
- ✅ Sin errores de conexión

---

## 🧪 Test rápido

1. Abre el dashboard
2. Click: "Búsqueda rápida"
3. Espera 2-3 minutos
4. Deberías ver ofertas (si hay en la BD)

---

## 📝 Notas importantes

### Base de datos en Railway

- Railway proporciona un **disco temporal**
- La BD se resetea cada deploy (opcional)
- Para persistencia, agregar PostgreSQL (gratis limitado)

### Actualizaciones

Si cambias código:
```bash
git add .
git commit -m "Tu mensaje"
git push
```

Automáticamente:
- Railway redeploya backend
- Vercel redeploya frontend

### Monitoreo

Railway te muestra:
- Logs en tiempo real
- Uso de CPU/memoria
- Errores

---

## 🚀 URLs finales

**Backend:** `https://job-search-automation-production.up.railway.app`  
**Frontend:** `https://job-search-automation.vercel.app`

Comparte el URL del frontend con quien quieras. ¡Todos pueden acceder!

---

## 💡 Próximos pasos

1. ✅ Backend en Railway
2. ✅ Frontend en Vercel
3. ⏳ Agregar base de datos persistente (PostgreSQL)
4. ⏳ Configurar scraping programado
5. ⏳ Agregar notificaciones

---

## 🆘 Troubleshooting

### "Error: Cannot find module"
```bash
pip install -r requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### "CORS error" o "Cannot reach API"
Asegúrate de:
1. Cambiar localhost a URL de Railway en HTML
2. Hacer git push
3. Esperar a que Vercel redeploy

### "Database error"
Railway usa un disco temporal. Los datos se pierden en cada deploy. Para persistencia:
1. Agregar PostgreSQL en Railway (gratis plan)
2. Cambiar `jobs.db` a PostgreSQL

---

## 📞 Necesitas ayuda?

1. **Railway:** https://railway.app/docs
2. **Vercel:** https://vercel.com/docs
3. **GitHub:** https://docs.github.com

---

**Versión:** 1.0 Deployment  
**Fecha:** Agosto 2026  
**Status:** ✅ Funcional
