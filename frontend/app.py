"""
🖥️ N1G Scraper - Panel de Visualización
========================================
Frontend de escritorio para visualizar productos scrapeados.
Usa CustomTkinter para un aspecto moderno y elegante.
"""

import customtkinter as ctk
from PIL import Image, ImageTk
import json
import threading
import io
import os
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request
import ssl

# Configuración de CustomTkinter
ctk.set_appearance_mode("dark")  # "dark", "light", "system"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

# Colores personalizados
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_card": "#16213e",
    "bg_sidebar": "#0f0f23",
    "accent": "#00d9ff",
    "accent_hover": "#00b8d4",
    "text": "#ffffff",
    "text_secondary": "#a0a0a0",
    "success": "#00e676",
    "warning": "#ffc107",
    "price": "#00e676",
}


class ImageLoader:
    """Carga imágenes desde URL de forma asíncrona con caché"""
    
    _cache: Dict[str, Image.Image] = {}
    _loading: set = set()
    
    @classmethod
    def load_async(cls, url: str, callback, size: tuple = (200, 200)):
        """Carga una imagen de forma asíncrona"""
        if not url or url in cls._loading:
            return
        
        if url in cls._cache:
            callback(cls._cache[url])
            return
        
        cls._loading.add(url)
        
        def _load():
            try:
                # Crear contexto SSL que no verifica certificados (para desarrollo)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                    data = response.read()
                    image = Image.open(io.BytesIO(data))
                    image = image.resize(size, Image.Resampling.LANCZOS)
                    cls._cache[url] = image
                    callback(image)
            except Exception as e:
                print(f"Error cargando imagen: {e}")
            finally:
                cls._loading.discard(url)
        
        thread = threading.Thread(target=_load, daemon=True)
        thread.start()


class ProductCard(ctk.CTkFrame):
    """Tarjeta individual de producto"""
    
    def __init__(self, parent, product: dict, on_click=None):
        super().__init__(parent, corner_radius=15, fg_color=COLORS["bg_card"])
        self.product = product
        self.on_click = on_click
        self.image_label = None
        
        self._create_widgets()
        self._load_image()
        
        # Hacer clickeable
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _create_widgets(self):
        # Contenedor de imagen
        self.image_frame = ctk.CTkFrame(self, fg_color="transparent", height=180)
        self.image_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.image_frame.pack_propagate(False)
        
        # Placeholder de imagen
        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="🖼️ Cargando...",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        self.image_label.pack(expand=True)
        
        # Título
        titulo = self.product.get("titulo") or self.product.get("title") or "Sin título"
        if titulo and len(titulo) > 50:
            titulo = titulo[:47] + "..."
        
        self.title_label = ctk.CTkLabel(
            self,
            text=titulo or "Sin título",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"],
            wraplength=220,
            justify="left"
        )
        self.title_label.pack(fill="x", padx=10, pady=(5, 2))
        
        # Precio
        precio = self.product.get("precio") or self.product.get("price_content") or "N/A"
        if precio and precio != "N/A":
            try:
                precio_num = int(float(str(precio).replace(".", "").replace(",", "")))
                precio = f"${precio_num:,}".replace(",", ".")
            except:
                pass
        
        self.price_label = ctk.CTkLabel(
            self,
            text=precio,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["price"]
        )
        self.price_label.pack(anchor="w", padx=10)
        
        # Stock y Score
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        stock = self.product.get("stock")
        stock_text = f"📦 {stock} und." if stock else "📦 Sin stock"
        stock_color = COLORS["success"] if stock else COLORS["warning"]
        
        ctk.CTkLabel(
            info_frame,
            text=stock_text,
            font=ctk.CTkFont(size=11),
            text_color=stock_color
        ).pack(side="left")
        
        score = self.product.get("score", 0)
        ctk.CTkLabel(
            info_frame,
            text=f"⭐ {score}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["accent"]
        ).pack(side="right")
    
    def _load_image(self):
        images = self.product.get("images", [])
        if images:
            ImageLoader.load_async(images[0], self._set_image, size=(200, 160))
    
    def _set_image(self, pil_image: Image.Image):
        try:
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(200, 160))
            self.image_label.configure(image=ctk_image, text="")
            self.image_label.image = ctk_image  # Mantener referencia
        except Exception as e:
            print(f"Error mostrando imagen: {e}")
    
    def _on_click(self, event):
        if self.on_click:
            self.on_click(self.product)
    
    def _on_enter(self, event):
        self.configure(fg_color="#1e3a5f")
    
    def _on_leave(self, event):
        self.configure(fg_color=COLORS["bg_card"])


class ProductDetailView(ctk.CTkToplevel):
    """Ventana de detalle de producto"""
    
    def __init__(self, parent, product: dict):
        super().__init__(parent)
        self.product = product
        
        self.title(product.get("titulo", "Detalle del Producto")[:60])
        self.geometry("800x700")
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Centrar ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 800) // 2
        y = (self.winfo_screenheight() - 700) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        self._load_images()
        
        self.grab_set()  # Modal
    
    def _create_widgets(self):
        # Contenedor principal con scroll
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Galería de imágenes
        self.gallery_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_card"], corner_radius=15, height=350)
        self.gallery_frame.pack(fill="x", pady=(0, 20))
        self.gallery_frame.pack_propagate(False)
        
        self.main_image_label = ctk.CTkLabel(
            self.gallery_frame,
            text="🖼️ Cargando imagen...",
            font=ctk.CTkFont(size=16)
        )
        self.main_image_label.pack(expand=True, pady=20)
        
        # Miniaturas
        self.thumbnails_frame = ctk.CTkFrame(self.gallery_frame, fg_color="transparent")
        self.thumbnails_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Info del producto
        info_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_card"], corner_radius=15)
        info_frame.pack(fill="x", pady=(0, 20))
        
        # Título
        ctk.CTkLabel(
            info_frame,
            text=self.product.get("titulo", "Sin título"),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text"],
            wraplength=700,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Precio grande
        precio = self.product.get("precio") or self.product.get("price_content") or "N/A"
        if precio and precio != "N/A":
            try:
                precio_num = int(float(str(precio).replace(".", "").replace(",", "")))
                precio = f"${precio_num:,}".replace(",", ".")
            except:
                pass
        
        ctk.CTkLabel(
            info_frame,
            text=precio,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["price"]
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        # Stock y Score
        stats_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        stock = self.product.get("stock")
        stock_text = f"📦 Stock: {stock} unidades" if stock else "📦 Sin stock disponible"
        stock_color = COLORS["success"] if stock else COLORS["warning"]
        
        ctk.CTkLabel(
            stats_frame,
            text=stock_text,
            font=ctk.CTkFont(size=14),
            text_color=stock_color
        ).pack(side="left", padx=(0, 30))
        
        score = self.product.get("score", 0)
        ctk.CTkLabel(
            stats_frame,
            text=f"⭐ Score: {score}/100",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["accent"]
        ).pack(side="left")
        
        category = self.product.get("category", "")
        if category:
            ctk.CTkLabel(
                stats_frame,
                text=f"📂 {category.capitalize()}",
                font=ctk.CTkFont(size=14),
                text_color=COLORS["text_secondary"]
            ).pack(side="right")
        
        # Descripción
        desc = self.product.get("description", "")
        if desc:
            desc_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_card"], corner_radius=15)
            desc_frame.pack(fill="x", pady=(0, 20))
            
            ctk.CTkLabel(
                desc_frame,
                text="📝 Descripción",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS["accent"]
            ).pack(anchor="w", padx=20, pady=(15, 5))
            
            ctk.CTkLabel(
                desc_frame,
                text=desc,
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"],
                wraplength=700,
                justify="left"
            ).pack(anchor="w", padx=20, pady=(0, 15))
        
        # URL
        url = self.product.get("url", "")
        if url and not url.startswith("file://"):
            url_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_card"], corner_radius=15)
            url_frame.pack(fill="x")
            
            ctk.CTkLabel(
                url_frame,
                text="🔗 URL del producto:",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"]
            ).pack(anchor="w", padx=20, pady=(10, 0))
            
            ctk.CTkLabel(
                url_frame,
                text=url[:80] + "..." if len(url) > 80 else url,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["accent"]
            ).pack(anchor="w", padx=20, pady=(0, 10))
    
    def _load_images(self):
        images = self.product.get("images", [])
        if images:
            # Imagen principal
            ImageLoader.load_async(images[0], self._set_main_image, size=(400, 300))
            
            # Miniaturas
            for i, img_url in enumerate(images[:6]):
                ImageLoader.load_async(img_url, lambda img, idx=i: self._add_thumbnail(img, idx), size=(60, 60))
    
    def _set_main_image(self, pil_image: Image.Image):
        try:
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(400, 300))
            self.main_image_label.configure(image=ctk_image, text="")
            self.main_image_label.image = ctk_image
        except Exception as e:
            print(f"Error: {e}")
    
    def _add_thumbnail(self, pil_image: Image.Image, index: int):
        try:
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(60, 60))
            label = ctk.CTkLabel(self.thumbnails_frame, image=ctk_image, text="")
            label.image = ctk_image
            label.pack(side="left", padx=5)
        except Exception as e:
            print(f"Error thumbnail: {e}")


class App(ctk.CTk):
    """Aplicación principal"""
    
    def __init__(self):
        super().__init__()
        
        self.title("🕷️ N1G Scraper - Panel de Control")
        self.geometry("1400x900")
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Datos
        self.categories: Dict[str, List[dict]] = {}
        self.all_products: List[dict] = []
        self.current_category: str = "all"
        self.search_query: str = ""
        
        # Centrar ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1400) // 2
        y = (self.winfo_screenheight() - 900) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_layout()
        self._load_data()
    
    def _create_layout(self):
        # Grid principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self._create_sidebar()
        
        # Contenido principal
        self._create_main_content()
    
    def _create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        
        # Logo/Título
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            logo_frame,
            text="🕷️ N1G Scraper",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            logo_frame,
            text="Panel de Visualización",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        
        # Separador
        ctk.CTkFrame(sidebar, height=2, fg_color=COLORS["bg_card"]).pack(fill="x", padx=20, pady=10)
        
        # Búsqueda
        self.search_entry = ctk.CTkEntry(
            sidebar,
            placeholder_text="🔍 Buscar productos...",
            height=40,
            corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["accent"],
            border_width=1
        )
        self.search_entry.pack(fill="x", padx=20, pady=(10, 20))
        self.search_entry.bind("<KeyRelease>", self._on_search)
        
        # Título categorías
        ctk.CTkLabel(
            sidebar,
            text="📂 CATEGORÍAS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        # Frame para botones de categorías
        self.categories_frame = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            scrollbar_button_color=COLORS["accent"]
        )
        self.categories_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Botón "Todas"
        self.category_buttons: Dict[str, ctk.CTkButton] = {}
        self._add_category_button("all", "🏠 Todas las categorías", 0)
        
        # Estadísticas en la parte inferior
        stats_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"], corner_radius=10)
        stats_frame.pack(fill="x", padx=20, pady=20)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="📊 Cargando datos...",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.stats_label.pack(pady=15)
        
        # Botón refrescar
        ctk.CTkButton(
            sidebar,
            text="🔄 Refrescar Datos",
            command=self._load_data,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            height=40,
            corner_radius=10
        ).pack(fill="x", padx=20, pady=(0, 20))
    
    def _add_category_button(self, key: str, text: str, count: int):
        btn = ctk.CTkButton(
            self.categories_frame,
            text=f"{text} ({count})" if count > 0 else text,
            anchor="w",
            fg_color="transparent" if key != self.current_category else COLORS["accent"],
            hover_color=COLORS["bg_card"],
            text_color=COLORS["text"],
            height=40,
            corner_radius=8,
            command=lambda k=key: self._select_category(k)
        )
        btn.pack(fill="x", pady=2)
        self.category_buttons[key] = btn
    
    def _create_main_content(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.title_label = ctk.CTkLabel(
            header,
            text="🏠 Todos los Productos",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text"]
        )
        self.title_label.pack(side="left")
        
        self.count_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        self.count_label.pack(side="right")
        
        # Grid de productos con scroll
        self.products_frame = ctk.CTkScrollableFrame(
            main,
            fg_color="transparent",
            scrollbar_button_color=COLORS["accent"]
        )
        self.products_frame.grid(row=1, column=0, sticky="nsew")
    
    def _load_data(self):
        """Carga datos desde los archivos JSON"""
        self.all_products = []
        self.categories = {}
        
        # Buscar directorio de datos
        base_path = Path(__file__).parent.parent
        categories_path = base_path / "data" / "categories"
        output_path = base_path / "output" / "output.json"
        
        # Cargar JSONs de categorías
        if categories_path.exists():
            for json_file in categories_path.glob("*.json"):
                if json_file.name.startswith("_"):
                    continue
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "products" in data:
                            cat_name = data.get("category", json_file.stem)
                            products = data["products"]
                        elif isinstance(data, list):
                            cat_name = json_file.stem
                            products = data
                        else:
                            continue
                        
                        self.categories[cat_name] = products
                        self.all_products.extend(products)
                except Exception as e:
                    print(f"Error cargando {json_file}: {e}")
        
        # Cargar output.json si existe y no hay categorías
        if not self.categories and output_path.exists():
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.all_products = data
                        # Agrupar por categoría si existe
                        for p in data:
                            cat = p.get("category", "otros")
                            if cat not in self.categories:
                                self.categories[cat] = []
                            self.categories[cat].append(p)
            except Exception as e:
                print(f"Error cargando output.json: {e}")
        
        # Actualizar UI
        self._update_category_buttons()
        self._update_stats()
        self._display_products()
    
    def _update_category_buttons(self):
        """Actualiza los botones de categorías"""
        # Limpiar botones existentes (excepto "all")
        for key, btn in list(self.category_buttons.items()):
            if key != "all":
                btn.destroy()
                del self.category_buttons[key]
        
        # Actualizar botón "all"
        if "all" in self.category_buttons:
            self.category_buttons["all"].configure(
                text=f"🏠 Todas las categorías ({len(self.all_products)})"
            )
        
        # Crear botones para cada categoría
        icons = {
            "computacion": "💻", "componentes": "🔧", "perifericos": "🖱️",
            "monitores": "🖥️", "notebooks": "💻", "almacenamiento": "💾",
            "redes": "📡", "gaming": "🎮", "impresoras": "🖨️",
            "accesorios": "🎧", "otros": "📦"
        }
        
        for cat_name, products in sorted(self.categories.items()):
            icon = icons.get(cat_name.lower(), "📦")
            self._add_category_button(cat_name, f"{icon} {cat_name.capitalize()}", len(products))
    
    def _update_stats(self):
        """Actualiza las estadísticas"""
        total = len(self.all_products)
        cats = len(self.categories)
        with_stock = sum(1 for p in self.all_products if p.get("stock"))
        
        self.stats_label.configure(
            text=f"📊 {total} productos\n📂 {cats} categorías\n📦 {with_stock} con stock"
        )
    
    def _select_category(self, category: str):
        """Selecciona una categoría"""
        self.current_category = category
        
        # Actualizar apariencia de botones
        for key, btn in self.category_buttons.items():
            if key == category:
                btn.configure(fg_color=COLORS["accent"])
            else:
                btn.configure(fg_color="transparent")
        
        # Actualizar título
        if category == "all":
            self.title_label.configure(text="🏠 Todos los Productos")
        else:
            icons = {
                "computacion": "💻", "componentes": "🔧", "perifericos": "🖱️",
                "monitores": "🖥️", "notebooks": "💻", "almacenamiento": "💾",
                "redes": "📡", "gaming": "🎮", "impresoras": "🖨️",
                "accesorios": "🎧", "otros": "📦"
            }
            icon = icons.get(category.lower(), "📦")
            self.title_label.configure(text=f"{icon} {category.capitalize()}")
        
        self._display_products()
    
    def _on_search(self, event=None):
        """Maneja la búsqueda"""
        self.search_query = self.search_entry.get().lower()
        self._display_products()
    
    def _display_products(self):
        """Muestra los productos en el grid"""
        # Limpiar grid actual
        for widget in self.products_frame.winfo_children():
            widget.destroy()
        
        # Filtrar productos
        if self.current_category == "all":
            products = self.all_products
        else:
            products = self.categories.get(self.current_category, [])
        
        # Aplicar búsqueda
        if self.search_query:
            products = [
                p for p in products
                if self.search_query in (p.get("titulo", "") or "").lower()
                or self.search_query in (p.get("description", "") or "").lower()
            ]
        
        # Actualizar contador
        self.count_label.configure(text=f"{len(products)} productos")
        
        # Crear grid de productos
        columns = 4
        for i, product in enumerate(products):
            row = i // columns
            col = i % columns
            
            card = ProductCard(
                self.products_frame,
                product,
                on_click=self._show_product_detail
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Configurar columnas
        for i in range(columns):
            self.products_frame.grid_columnconfigure(i, weight=1)
        
        # Mensaje si no hay productos
        if not products:
            ctk.CTkLabel(
                self.products_frame,
                text="😕 No se encontraron productos",
                font=ctk.CTkFont(size=18),
                text_color=COLORS["text_secondary"]
            ).grid(row=0, column=0, columnspan=4, pady=100)
    
    def _show_product_detail(self, product: dict):
        """Muestra el detalle de un producto"""
        ProductDetailView(self, product)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
