# 🚀 Desplegar en Vercel - 3 Pasos (5 minutos)

**Tu app en internet, accesible desde cualquier lado.**

---

## 📋 PASO 1: Crear repositorio GitHub

### A. Ir a GitHub
```
https://github.com/new
```

### B. Llenar datos:
- **Repository name:** `job-search-automation`
- **Description:** Sistema de búsqueda automática de trabajo
- **Public:** ✅ Selecciona Public
- Click: **Create repository**

### C. Copiar URL
Te aparecerá algo como:
```
https://github.com/TU_USUARIO/job-search-automation.git
```

**COPIA ESA URL**

---

## 📋 PASO 2: Subir tu código a GitHub

Abre terminal en la carpeta del proyecto:
```bash
cd C:\Users\anama\Downloads\Github\job-search-automation
```

Ejecuta (reemplaza TU_USUARIO con tu usuario de GitHub):
```bash
git remote add origin https://github.com/TU_USUARIO/job-search-automation.git
git branch -M main
git push -u origin main
```

**Espera 2-3 minutos...**

Cuando termine, verás:
```
✓ Everything up-to-date
```

---

## 📋 PASO 3: Desplegar en Vercel

### A. Ir a Vercel
```
https://vercel.com
```

### B. Click en "Sign Up"
- Selecciona: **GitHub**
- Autoriza Vercel con tu GitHub

### C. Click: "New Project"

### D. Busca y selecciona
- Busca: `job-search-automation`
- Click para seleccionar

### E. Configurar proyecto
En la página de configuración:
- **Framework Preset:** Other (por defecto está bien)
- **Root Directory:** ./ (por defecto)
- No necesitas cambiar nada más

### F. Click: "Deploy"

**Espera 1-2 minutos...**

---

## ✅ ¡LISTO!

Verás la pantalla de éxito con tu URL:
```
https://job-search-automation.vercel.app
```

**Esa es tu app en internet!** 🎉

---

## 🔗 Resultado

Ahora tienes:
- ✅ Backend corriendo en Vercel
- ✅ Frontend corriendo en Vercel
- ✅ URL pública
- ✅ Accesible desde cualquier dispositivo
- ✅ Gratis

---

## 🧪 Test

Abre en navegador:
```
https://job-search-automation.vercel.app
```

Deberías ver:
- 💼 Título: "Job Search Automation"
- 🔍 Botones de búsqueda
- 📊 Estadísticas
- 💻 Todo funcionando

---

## 📝 Notas

### Si algo no funciona

**1. Errores de conexión a API**
- Vercel es solo para el frontend (HTML)
- El backend (Python) necesita otro hosting
- Para producción, usa Railway (ver DEPLOYMENT.md)

**2. Por ahora funciona como:**
- Frontend en Vercel ✅
- Backend local (en tu PC) 
- Solo si tu PC está corriendo `python -m web.app`

### Para producción COMPLETA:
- Seguir DEPLOYMENT.md (Railway + Vercel)

---

## 🎯 Próximos pasos

1. ✅ Frontend en Vercel (HECHO)
2. ⏳ Backend en Railway (ver DEPLOYMENT.md)
3. ⏳ Conectar backend + frontend

---

**¡Listo! Tu app está en internet** 🚀

Comparte la URL con quien quieras:
```
https://job-search-automation.vercel.app
```
