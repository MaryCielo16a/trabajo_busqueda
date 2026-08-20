#!/usr/bin/env python3
"""Interactive configuration wizard for Job Search Automation"""

import os
from pathlib import Path

COUNTRIES = {
    "1": {"name": "Colombia", "ct": "computrabajo.com.co", "bm": "bumeran.com.co"},
    "2": {"name": "Argentina", "ct": "computrabajo.com.ar", "bm": "bumeran.com.ar"},
    "3": {"name": "México", "ct": "computrabajo.com.mx", "bm": "bumeran.com.mx"},
    "4": {"name": "Chile", "ct": "computrabajo.cl", "bm": "bumeran.cl"},
    "5": {"name": "Perú", "ct": "computrabajo.com.pe", "bm": "bumeran.pe"},
    "6": {"name": "Otro", "ct": "manual", "bm": "manual"},
}

ROLES = {
    "1": {
        "name": "Frontend Developer",
        "keywords": "react,frontend,javascript,vue,angular,html,css,node.js,junior,trainee"
    },
    "2": {
        "name": "Backend Developer",
        "keywords": "backend,python,node.js,java,golang,api,rest,junior,trainee"
    },
    "3": {
        "name": "Full-stack Developer",
        "keywords": "full-stack,react,node.js,python,javascript,frontend,backend,junior"
    },
    "4": {
        "name": "Data Analyst",
        "keywords": "data analyst,python,sql,powerbi,excel,analisis de datos,junior"
    },
    "5": {
        "name": "Personalizado",
        "keywords": None  # Will ask user
    },
}

def print_header():
    print("\n" + "="*60)
    print("🚀 Job Search Automation - Configuración Inicial")
    print("="*60 + "\n")

def select_country():
    print("Selecciona tu país:")
    for key, country in COUNTRIES.items():
        print(f"  {key}. {country['name']}")

    choice = input("\nOpción (1-6): ").strip()

    if choice not in COUNTRIES:
        print("❌ Opción inválida")
        return select_country()

    country = COUNTRIES[choice]

    if country["ct"] == "manual":
        print("\nIngresa los URLs manuales:")
        ct_url = input("Computrabajo URL (ej: computrabajo.com.pe): ").strip()
        bm_url = input("Bumerán URL (ej: bumeran.pe): ").strip()

        return {
            "name": country["name"],
            "ct": f"https://www.{ct_url}",
            "bm": f"https://www.{bm_url}"
        }
    else:
        return {
            "name": country["name"],
            "ct": f"https://www.{country['ct']}",
            "bm": f"https://www.{country['bm']}"
        }

def select_role():
    print("\nSelecciona tu rol objetivo:")
    for key, role in ROLES.items():
        print(f"  {key}. {role['name']}")

    choice = input("\nOpción (1-5): ").strip()

    if choice not in ROLES:
        print("❌ Opción inválida")
        return select_role()

    role = ROLES[choice]

    if role["keywords"] is None:
        keywords = input("Ingresa tus palabras clave (separadas por comas): ").strip()
    else:
        keywords = role["keywords"]
        print(f"\n✓ Keywords: {keywords}")

    return {
        "name": role["name"],
        "keywords": keywords
    }

def ask_remote_only():
    while True:
        response = input("\n¿Buscar solo ofertas remoto? (s/n): ").strip().lower()
        if response in ["s", "si", "sí"]:
            return "true"
        elif response in ["n", "no"]:
            return "false"
        else:
            print("❌ Opción inválida. Ingresa 's' o 'n'")

def ask_apify():
    print("\n¿Tienes cuenta en Apify? (opcional, para mejor confiabilidad)")
    print("Apify es un servicio de scraping premium: https://apify.com")

    response = input("¿Tienes API key de Apify? (s/n): ").strip().lower()

    if response in ["s", "si", "sí"]:
        api_key = input("Ingresa tu APIFY_API_KEY: ").strip()
        return api_key

    return None

def save_env(country, role, remote_only, apify_key):
    env_content = f"""# Database configuration
DB_PATH=jobs.db

# Search preferences
REMOTE_ONLY={remote_only}

# Keywords to search (comma-separated)
KEYWORDS={role['keywords']}

# Experience level filter
MIN_EXPERIENCE_LEVEL=junior

# Scraping interval (in minutes)
SCRAPE_INTERVAL_MINUTES=60

# Apify configuration (optional)
"""

    if apify_key:
        env_content += f"APIFY_API_KEY={apify_key}\n"

    with open(".env", "w") as f:
        f.write(env_content)

    print(f"\n✓ Archivo .env creado correctamente")

def update_settings(country):
    settings_file = "config/settings.py"

    if not os.path.exists(settings_file):
        print(f"❌ No se encontró {settings_file}")
        return

    with open(settings_file, "r") as f:
        content = f.read()

    # Update URLs
    content = content.replace(
        'COMPUTRABAJO_BASE_URL = "https://www.computrabajo.com"',
        f'COMPUTRABAJO_BASE_URL = "{country["ct"]}"'
    )
    content = content.replace(
        'BUMERAN_BASE_URL = "https://www.bumeran.com.co"',
        f'BUMERAN_BASE_URL = "{country["bm"]}"'
    )

    with open(settings_file, "w") as f:
        f.write(content)

    print(f"✓ URLs actualizados en config/settings.py")

def main():
    print_header()

    print("Este asistente te ayudará a configurar el sistema.\n")

    # Select country
    country = select_country()
    print(f"✓ País seleccionado: {country['name']}")

    # Select role
    role = select_role()
    print(f"✓ Rol seleccionado: {role['name']}")

    # Remote only
    remote_only = ask_remote_only()
    print(f"✓ Solo remoto: {'Sí' if remote_only == 'true' else 'No'}")

    # Apify key
    apify_key = ask_apify()
    if apify_key:
        print(f"✓ Apify API key configurada")

    # Save configuration
    print("\n" + "="*60)
    print("Guardando configuración...")
    print("="*60)

    save_env(country, role, remote_only, apify_key)
    update_settings(country)

    print("\n" + "="*60)
    print("✅ ¡Configuración completada!")
    print("="*60)

    print(f"\nTus configuraciones:")
    print(f"  País: {country['name']}")
    print(f"  Rol: {role['name']}")
    print(f"  Solo remoto: {'Sí' if remote_only == 'true' else 'No'}")
    print(f"  Keywords: {role['keywords']}")

    print("\n📋 Próximos pasos:")
    print("  1. python run.py init          # Inicializar base de datos")
    print("  2. python run.py scrape        # Buscar ofertas")
    print("  3. python run.py list          # Ver ofertas filtradas")

    print("\n📖 Más información: lee SETUP.md y README.md\n")

if __name__ == "__main__":
    main()
