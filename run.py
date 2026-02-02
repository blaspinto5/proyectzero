#!/usr/bin/env python
"""
🕷️ N1G Scraper - Script Principal de Ejecución
==============================================

Este script simplifica la ejecución del scraper con comandos simples.

Uso:
    python run.py              # Scraping completo de todas las categorías
    python run.py --quick      # Solo 2 páginas por categoría (prueba rápida)
    python run.py --category computacion,gaming  # Solo categorías específicas
    python run.py --setup      # Solo configurar entorno (instalar deps, crear DB)
    python run.py --local      # Usar archivo HTML local para pruebas
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🕷️  N1G SCRAPER - Web Scraping para n1g.cl                  ║
║                                                               ║
║   Extrae productos, precios y stock de todas las categorías   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.END}
"""
    print(banner)

def run_command(cmd, description, cwd=None):
    """Ejecuta un comando mostrando progreso"""
    print(f"{Colors.BLUE}▶ {description}...{Colors.END}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or Path(__file__).parent,
            capture_output=False,
        )
        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ {description} completado{Colors.END}\n")
            return True
        else:
            print(f"{Colors.FAIL}✗ Error en: {description}{Colors.END}\n")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}✗ Error: {e}{Colors.END}\n")
        return False

def setup_environment():
    """Configura el entorno: dependencias, playwright, base de datos"""
    print(f"\n{Colors.HEADER}🔧 CONFIGURANDO ENTORNO{Colors.END}\n")
    
    steps = [
        ("pip install -r requirements.txt", "Instalando dependencias Python"),
        ("playwright install chromium", "Instalando navegador Chromium"),
        ("python manage_db.py upgrade", "Configurando base de datos"),
    ]
    
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            print(f"{Colors.WARNING}⚠ Advertencia: {desc} falló, continuando...{Colors.END}")
    
    print(f"{Colors.GREEN}✓ Entorno configurado correctamente{Colors.END}\n")

def run_scraper(args):
    """Ejecuta el spider según los argumentos"""
    print(f"\n{Colors.HEADER}🚀 INICIANDO SCRAPING{Colors.END}\n")
    
    # Construir comando de scrapy
    spider = "categories"
    cmd_parts = ["scrapy", "crawl", spider]
    
    if args.quick:
        cmd_parts.extend(["-a", "max_pages=2"])
        print(f"{Colors.CYAN}   Modo rápido: máximo 2 páginas por categoría{Colors.END}")
    
    if args.category:
        cmd_parts.extend(["-a", f"categories={args.category}"])
        print(f"{Colors.CYAN}   Categorías: {args.category}{Colors.END}")
    
    if args.local:
        # Modo local con HTML de prueba
        os.environ["DISABLE_PLAYWRIGHT"] = "1"
        spider = "n1g_spider"
        html_path = Path(__file__).parent / "projectzero2" / "html2222"
        html_files = list(html_path.glob("*.html"))
        if html_files:
            file_url = html_files[0].as_uri()
            cmd_parts = ["scrapy", "parse", "--spider=n1g_spider", "-c", "parse_product", f'"{file_url}"']
            print(f"{Colors.CYAN}   Modo local: usando archivo HTML de prueba{Colors.END}")
    
    cmd = " ".join(cmd_parts)
    print(f"{Colors.BLUE}   Comando: {cmd}{Colors.END}\n")
    
    return run_command(cmd, "Ejecutando spider")

def show_results():
    """Muestra resumen de resultados"""
    print(f"\n{Colors.HEADER}📊 RESULTADOS{Colors.END}\n")
    
    data_dir = Path(__file__).parent / "data" / "categories"
    output_dir = Path(__file__).parent / "output"
    
    # Contar archivos JSON de categorías
    if data_dir.exists():
        json_files = list(data_dir.glob("*.json"))
        print(f"{Colors.GREEN}   📁 Archivos de categorías: {len(json_files)}{Colors.END}")
        for f in json_files:
            if f.name != "_summary.json":
                print(f"      - {f.name}")
    
    # Mostrar archivos de output principal
    if output_dir.exists():
        print(f"\n{Colors.GREEN}   📁 Archivos de salida:{Colors.END}")
        for f in output_dir.iterdir():
            size = f.stat().st_size / 1024
            print(f"      - {f.name} ({size:.1f} KB)")
    
    # Mostrar base de datos
    db_file = Path(__file__).parent / "projectzero.db"
    if db_file.exists():
        size = db_file.stat().st_size / 1024
        print(f"\n{Colors.GREEN}   🗄️ Base de datos: projectzero.db ({size:.1f} KB){Colors.END}")

def main():
    parser = argparse.ArgumentParser(
        description="🕷️ N1G Scraper - Extrae productos de n1g.cl",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run.py                          # Scraping completo
  python run.py --quick                  # Prueba rápida (2 páginas)
  python run.py --category gaming        # Solo categoría gaming
  python run.py --setup                  # Configurar entorno
  python run.py --quick --category computacion,gaming
        """
    )
    
    parser.add_argument("--setup", action="store_true", help="Configurar entorno (deps, DB)")
    parser.add_argument("--quick", action="store_true", help="Modo rápido (2 páginas max)")
    parser.add_argument("--category", type=str, help="Categorías específicas (separadas por coma)")
    parser.add_argument("--local", action="store_true", help="Usar HTML local para pruebas")
    parser.add_argument("--no-banner", action="store_true", help="No mostrar banner")
    
    args = parser.parse_args()
    
    if not args.no_banner:
        print_banner()
    
    # Cambiar al directorio del proyecto
    os.chdir(Path(__file__).parent)
    
    if args.setup:
        setup_environment()
        return
    
    # Verificar que estamos en el proyecto correcto
    if not Path("scrapy.cfg").exists():
        print(f"{Colors.FAIL}❌ Error: No se encuentra scrapy.cfg. Ejecuta desde el directorio del proyecto.{Colors.END}")
        sys.exit(1)
    
    # Ejecutar scraper
    success = run_scraper(args)
    
    if success:
        show_results()
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Scraping completado exitosamente{Colors.END}\n")
    else:
        print(f"\n{Colors.WARNING}⚠ Scraping terminó con errores{Colors.END}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
