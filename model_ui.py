import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import model_backend as model_backend
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime
import numpy as np

class WildfireAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Análisis de Incendios")
        self.root.geometry("1200x800")
        
        # Variables
        self.current_year = tk.IntVar(value=2015)
        self.min_year = 2015
        self.max_year = 2023
        self.df = None
        self.canvases = {}
        self.tabs = {}
        
        # Configurar estilo
        self.setup_styles()
        
        # Load data
        try:
            self.df = model_backend.load_and_process_data('BD.csv')
            print("Datos cargados correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {str(e)}")
            return
        
        # Create main frames
        self.create_main_layout()
        self.create_year_selector()
        self.create_tabs()
        
        # Initial update
        self.update_all_visualizations()
    
    def setup_styles(self):
        style = ttk.Style()
        # Configurar estilo para botones de año
        style.configure("Year.TButton", font=("Arial", 12, "bold"), padding=10)
        style.configure("YearNav.TButton", font=("Arial", 14, "bold"), padding=5)
        style.configure("Selected.TButton", background="#4CAF50", foreground="white", font=("Arial", 12, "bold"))
    
    def create_main_layout(self):
        # Main container with two panels
        self.main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for controls
        self.left_frame = ttk.Frame(self.main_pane, padding="10", width=250)
        self.left_frame.pack_propagate(False)  # Prevent shrinking
        self.main_pane.add(self.left_frame, weight=1)
        
        # Right panel for visualizations
        self.right_frame = ttk.Frame(self.main_pane, padding="10")
        self.main_pane.add(self.right_frame, weight=4)
        
        # Status bar
        self.status_var = tk.StringVar(value="Listo")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_year_selector(self):
        # Year selector frame
        year_frame = ttk.LabelFrame(self.left_frame, text="Selección de Año", padding="10")
        year_frame.pack(fill=tk.X, pady=10)
        
        # Year navigation with prev/next buttons
        year_nav_frame = ttk.Frame(year_frame)
        year_nav_frame.pack(fill=tk.X, pady=10)
        
        # Previous year button
        self.prev_btn = ttk.Button(
            year_nav_frame,
            text="◀",
            style="YearNav.TButton",
            command=self.previous_year,
            width=3
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        # Year display (centered)
        self.year_display = ttk.Label(
            year_nav_frame,
            textvariable=self.current_year,
            font=("Arial", 18, "bold"),
            anchor=tk.CENTER,
            width=6
        )
        self.year_display.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        
        # Next year button
        self.next_btn = ttk.Button(
            year_nav_frame,
            text="▶",
            style="YearNav.TButton",
            command=self.next_year,
            width=3
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        
        # Year range label
        ttk.Label(
            year_frame,
            text=f"Rango: {self.min_year} - {self.max_year}",
            anchor=tk.CENTER
        ).pack(fill=tk.X, pady=5)
        
        # Historical analysis section
        hist_frame = ttk.LabelFrame(self.left_frame, text="Análisis Histórico (2015-2023)", padding="10")
        hist_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            hist_frame, 
            text="Ver Análisis Histórico Completo",
            command=self.show_historical_analysis
        ).pack(fill=tk.X, pady=5)
        
        ttk.Button(
            hist_frame, 
            text="Matriz de Riesgo Histórica",
            command=self.show_historical_risk_matrix
        ).pack(fill=tk.X, pady=5)
        
        ttk.Button(
            hist_frame, 
            text="Resumen de Datos Históricos",
            command=self.show_historical_summary
        ).pack(fill=tk.X, pady=5)
        
        # Sección para leyendas de clusters con scrollbars
        self.legend_frame = ttk.LabelFrame(self.left_frame, text="Leyendas", padding="10")
        self.legend_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Crear un notebook para las leyendas
        self.legend_notebook = ttk.Notebook(self.legend_frame)
        self.legend_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña para leyenda regional
        self.regional_legend_tab = ttk.Frame(self.legend_notebook)
        self.legend_notebook.add(self.regional_legend_tab, text="Regional")
        
        # Pestaña para leyenda individual
        self.individual_legend_tab = ttk.Frame(self.legend_notebook)
        self.legend_notebook.add(self.individual_legend_tab, text="Individual")
        
        # Crear canvas con scrollbar para leyenda regional
        self.regional_legend_canvas = tk.Canvas(self.regional_legend_tab)
        regional_legend_scrollbar = ttk.Scrollbar(self.regional_legend_tab, orient="vertical", command=self.regional_legend_canvas.yview)
        regional_legend_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.regional_legend_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.regional_legend_canvas.configure(yscrollcommand=regional_legend_scrollbar.set)
        
        # Frame dentro del canvas para el contenido de la leyenda regional
        self.regional_legend_frame = ttk.Frame(self.regional_legend_canvas)
        self.regional_legend_canvas.create_window((0, 0), window=self.regional_legend_frame, anchor="nw")
        self.regional_legend_frame.bind("<Configure>", lambda e: self.regional_legend_canvas.configure(scrollregion=self.regional_legend_canvas.bbox("all")))
        
        # Crear canvas con scrollbar para leyenda individual
        self.individual_legend_canvas = tk.Canvas(self.individual_legend_tab)
        individual_legend_scrollbar = ttk.Scrollbar(self.individual_legend_tab, orient="vertical", command=self.individual_legend_canvas.yview)
        individual_legend_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.individual_legend_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.individual_legend_canvas.configure(yscrollcommand=individual_legend_scrollbar.set)
        
        # Frame dentro del canvas para el contenido de la leyenda individual
        self.individual_legend_frame = ttk.Frame(self.individual_legend_canvas)
        self.individual_legend_canvas.create_window((0, 0), window=self.individual_legend_frame, anchor="nw")
        self.individual_legend_frame.bind("<Configure>", lambda e: self.individual_legend_canvas.configure(scrollregion=self.individual_legend_canvas.bbox("all")))
    
    def previous_year(self):
        current = self.current_year.get()
        if current > self.min_year:
            self.current_year.set(current - 1)
            self.update_all_visualizations()
    
    def next_year(self):
        current = self.current_year.get()
        if current < self.max_year:
            self.current_year.set(current + 1)
            self.update_all_visualizations()
    
    def create_tabs(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tabs["clusters"] = ttk.Frame(self.notebook)
        self.tabs["matrix"] = ttk.Frame(self.notebook)
        self.tabs["summary"] = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tabs["clusters"], text="Clusters")
        self.notebook.add(self.tabs["matrix"], text="Matriz de Riesgo")
        self.notebook.add(self.tabs["summary"], text="Resumen")
        
        # Setup clusters tab with VERTICAL layout and scrollbars
        clusters_frame = ttk.Frame(self.tabs["clusters"])
        clusters_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a canvas with scrollbar for the clusters
        self.clusters_canvas = tk.Canvas(clusters_frame)
        clusters_scrollbar = ttk.Scrollbar(clusters_frame, orient="vertical", command=self.clusters_canvas.yview)
        clusters_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.clusters_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.clusters_canvas.configure(yscrollcommand=clusters_scrollbar.set)
        
        # Frame inside canvas for content
        self.clusters_content_frame = ttk.Frame(self.clusters_canvas)
        self.clusters_canvas.create_window((0, 0), window=self.clusters_content_frame, anchor="nw")
        
        # Regional clusters frame
        regional_frame = ttk.LabelFrame(self.clusters_content_frame, text="Clusters Regionales")
        regional_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Individual clusters frame
        individual_frame = ttk.LabelFrame(self.clusters_content_frame, text="Clusters Individuales")
        individual_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Create canvas placeholders with fixed size
        self.canvases["regional"] = self.create_canvas_placeholder(regional_frame, width=1000, height=400)
        self.canvases["individual"] = self.create_canvas_placeholder(individual_frame, width=1000, height=400)
        
        # Configure the canvas to update scroll region when the size of the content frame changes
        self.clusters_content_frame.bind("<Configure>", self.on_clusters_frame_configure)
        
        # Setup matrix tab with scrollbar
        matrix_frame = ttk.Frame(self.tabs["matrix"])
        matrix_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a canvas with scrollbar for the matrix
        self.matrix_canvas = tk.Canvas(matrix_frame)
        matrix_scrollbar = ttk.Scrollbar(matrix_frame, orient="vertical", command=self.matrix_canvas.yview)
        matrix_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.matrix_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.matrix_canvas.configure(yscrollcommand=matrix_scrollbar.set)
        
        # Frame inside canvas for content
        self.matrix_content_frame = ttk.Frame(self.matrix_canvas)
        self.matrix_canvas.create_window((0, 0), window=self.matrix_content_frame, anchor="nw")
        
        # Create matrix placeholder
        self.canvases["matrix"] = self.create_canvas_placeholder(self.matrix_content_frame, width=800, height=600)
        
        # Configure the canvas to update scroll region when the size of the content frame changes
        self.matrix_content_frame.bind("<Configure>", self.on_matrix_frame_configure)
        
        # Setup summary tab
        summary_frame = ttk.Frame(self.tabs["summary"])
        summary_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text widgets for summary data
        top10_frame = ttk.LabelFrame(summary_frame, text="Top 10 Regiones")
        top10_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5, pady=5)
        
        eco_frame = ttk.LabelFrame(summary_frame, text="Resumen de Ecosistemas")
        eco_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, padx=5, pady=5)
        
        self.top10_text = scrolledtext.ScrolledText(top10_frame, width=40, height=20)
        self.top10_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.eco_text = scrolledtext.ScrolledText(eco_frame, width=40, height=20)
        self.eco_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def on_clusters_frame_configure(self, event):
        """Actualiza la región de desplazamiento del canvas de clusters"""
        self.clusters_canvas.configure(scrollregion=self.clusters_canvas.bbox("all"))
    
    def on_matrix_frame_configure(self, event):
        """Actualiza la región de desplazamiento del canvas de matriz"""
        self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all"))
    
    def create_canvas_placeholder(self, parent, width=800, height=600):
        """Crea un placeholder para el canvas con tamaño fijo"""
        # Crear un frame contenedor con padding
        container_frame = ttk.Frame(parent, padding=10, width=width, height=height)
        container_frame.pack(padx=5, pady=5)
        container_frame.pack_propagate(False)  # Mantener el tamaño fijo
        
        # Crear la figura con tamaño fijo
        fig = Figure(figsize=(width/100, height/100), dpi=100)
        
        # Crear el canvas
        canvas = FigureCanvasTkAgg(fig, master=container_frame)
        
        # Empaquetar el widget del canvas
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        return {"figure": fig, "canvas": canvas, "frame": container_frame}
    
    def update_all_visualizations(self):
        self.status_var.set(f"Actualizando visualizaciones para el año {self.current_year.get()}...")
        self.root.update_idletasks()
        
        # Limpiar leyendas anteriores
        for widget in self.regional_legend_frame.winfo_children():
            widget.destroy()
        for widget in self.individual_legend_frame.winfo_children():
            widget.destroy()
        
        # Update all visualizations for the selected year
        self.update_regional_clusters()
        self.update_individual_clusters()
        self.update_risk_matrix()
        self.update_summary_data()
        
        self.status_var.set(f"Visualizaciones actualizadas para el año {self.current_year.get()}")
    
    def update_regional_clusters(self):
        try:
            year = self.current_year.get()
            reg_summary = model_backend.get_regional_summary_by_year(self.df, year)
            reg_summary = model_backend.compute_regional_clusters(reg_summary)
            
            # Obtener la figura y limpiarla
            fig = self.canvases["regional"]["figure"]
            fig.clear()
            
            # Crear un nuevo subplot que ocupe toda la figura
            ax = fig.add_subplot(111)
            
            # Crear el scatter plot con tamaños adecuados
            scatter = sns.scatterplot(
                x='Longitud_round', y='Latitud_round', 
                hue='cluster_region', size='frecuencia_incendios', 
                sizes=(20, 200), palette='viridis', 
                data=reg_summary, alpha=0.7, ax=ax,
                legend=False  # No mostrar leyenda en el gráfico
            )
            
            # Configurar el título y etiquetas
            ax.set_title(f'Clusters Regionales - Año {year}', fontsize=16, pad=20)
            ax.set_xlabel('Longitud', fontsize=14)
            ax.set_ylabel('Latitud', fontsize=14)
            
            # Ajustar los límites del gráfico
            ax.set_aspect('equal')  # Mantener la proporción correcta
            
            # Ajustar el layout para que todo quepa
            fig.tight_layout()
            
            # Redibujar el canvas
            self.canvases["regional"]["canvas"].draw()
            
            # Crear leyenda en el panel izquierdo
            ttk.Label(self.regional_legend_frame, text=f"Clusters Regionales - Año {year}", font=("Arial", 12, "bold")).pack(pady=5)
            
            # Crear leyenda para clusters regionales
            unique_clusters = reg_summary['cluster_region'].unique()
            colors = plt.cm.viridis(np.linspace(0, 1, len(unique_clusters)))
            
            for i, cluster in enumerate(sorted(unique_clusters)):
                cluster_frame = ttk.Frame(self.regional_legend_frame)
                cluster_frame.pack(fill=tk.X, pady=2)
                
                # Crear un cuadrado de color para el cluster
                color_canvas = tk.Canvas(cluster_frame, width=15, height=15, bg=self.rgb_to_hex(colors[i][:3]))
                color_canvas.pack(side=tk.LEFT, padx=5)
                
                # Etiqueta con el número de cluster
                ttk.Label(cluster_frame, text=f"Cluster {cluster}").pack(side=tk.LEFT, padx=5)
            
            # Leyenda para tamaño de puntos
            ttk.Label(self.regional_legend_frame, text="Frecuencia de Incendios", font=("Arial", 10, "bold")).pack(pady=5)
            
            # Mostrar rangos de frecuencia
            freq_ranges = [(15, "Baja"), (45, "Media"), (75, "Alta")]
            for size, label in freq_ranges:
                size_frame = ttk.Frame(self.regional_legend_frame)
                size_frame.pack(fill=tk.X, pady=2)
                
                # Crear un círculo proporcional al tamaño
                size_canvas = tk.Canvas(size_frame, width=30, height=20)
                size_canvas.pack(side=tk.LEFT, padx=5)
                radius = min(size / 3, 8)  # Escalar el radio para que quepa
                size_canvas.create_oval(15-radius, 10-radius, 15+radius, 10+radius, fill="gray")
                
                # Etiqueta con el rango
                ttk.Label(size_frame, text=f"{label} ({size})").pack(side=tk.LEFT, padx=5)
            
            # Actualizar la región de desplazamiento del canvas de leyenda
            self.regional_legend_canvas.configure(scrollregion=self.regional_legend_canvas.bbox("all"))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar datos regionales: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_individual_clusters(self):
        try:
            year = self.current_year.get()
            data_year, _ = model_backend.get_individual_summary_by_year(self.df, year)
            
            # Obtener la figura y limpiarla
            fig = self.canvases["individual"]["figure"]
            fig.clear()
            
            # Crear un nuevo subplot que ocupe toda la figura
            ax = fig.add_subplot(111)
            
            # Crear el scatter plot con tamaños adecuados
            scatter = sns.scatterplot(
                x='Longitud', y='Latitud', 
                hue='cluster_incendio', size='Duración días', 
                sizes=(10, 100), palette='plasma', 
                data=data_year, alpha=0.5, ax=ax,
                legend=False  # No mostrar leyenda en el gráfico
            )
            
            # Configurar el título y etiquetas
            ax.set_title(f'Clusters Individuales - Año {year}', fontsize=16, pad=20)
            ax.set_xlabel('Longitud', fontsize=14)
            ax.set_ylabel('Latitud', fontsize=14)
            
            # Ajustar los límites del gráfico
            ax.set_aspect('equal')  # Mantener la proporción correcta
            
            # Ajustar el layout para que todo quepa
            fig.tight_layout()
            
            # Redibujar el canvas
            self.canvases["individual"]["canvas"].draw()
            
            # Crear leyenda en el panel izquierdo
            ttk.Label(self.individual_legend_frame, text=f"Clusters Individuales - Año {year}", font=("Arial", 12, "bold")).pack(pady=5)
            
            # Crear leyenda para clusters individuales
            unique_clusters = data_year['cluster_incendio'].unique()
            colors = plt.cm.plasma(np.linspace(0, 1, len(unique_clusters)))
            
            for i, cluster in enumerate(sorted(unique_clusters)):
                cluster_frame = ttk.Frame(self.individual_legend_frame)
                cluster_frame.pack(fill=tk.X, pady=2)
                
                # Crear un cuadrado de color para el cluster
                color_canvas = tk.Canvas(cluster_frame, width=15, height=15, bg=self.rgb_to_hex(colors[i][:3]))
                color_canvas.pack(side=tk.LEFT, padx=5)
                
                # Etiqueta con el número de cluster
                ttk.Label(cluster_frame, text=f"Cluster {cluster}").pack(side=tk.LEFT, padx=5)
            
            # Leyenda para tamaño de puntos
            ttk.Label(self.individual_legend_frame, text="Duración (días)", font=("Arial", 10, "bold")).pack(pady=5)
            
            # Mostrar rangos de duración
            duration_ranges = [(1, "Corta"), (5, "Media"), (10, "Larga")]
            for size, label in duration_ranges:
                size_frame = ttk.Frame(self.individual_legend_frame)
                size_frame.pack(fill=tk.X, pady=2)
                
                # Crear un círculo proporcional al tamaño
                size_canvas = tk.Canvas(size_frame, width=30, height=20)
                size_canvas.pack(side=tk.LEFT, padx=5)
                radius = min(size * 2, 8)  # Escalar el radio para que quepa
                size_canvas.create_oval(15-radius, 10-radius, 15+radius, 10+radius, fill="gray")
                
                # Etiqueta con el rango
                ttk.Label(size_frame, text=f"{label} ({size} días)").pack(side=tk.LEFT, padx=5)
            
            # Actualizar la región de desplazamiento del canvas de leyenda
            self.individual_legend_canvas.configure(scrollregion=self.individual_legend_canvas.bbox("all"))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar datos individuales: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def rgb_to_hex(self, rgb):
        """Convierte valores RGB (0-1) a formato hexadecimal para Tkinter"""
        r, g, b = [int(x * 255) for x in rgb]
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def update_risk_matrix(self):
        try:
            year = self.current_year.get()
            risk_matrix = model_backend.compute_risk_matrix_by_year(self.df, year)
            
            fig = self.canvases["matrix"]["figure"]
            fig.clear()
            ax = fig.add_subplot(111)
            
            # Verificar si la matriz de riesgo está vacía
            if risk_matrix.empty:
                ax.text(0.5, 0.5, f"No hay datos suficientes para generar la matriz de riesgo en {year}",
                        transform=ax.transAxes, ha="center", va="center", fontsize=16)
            else:
                # Crear el heatmap con anotaciones
                sns.heatmap(
                    risk_matrix, annot=True, fmt='g', 
                    cmap='YlOrRd', ax=ax,
                    cbar_kws={'label': 'Nivel de Riesgo'}
                )
                ax.set_title(f'Matriz de Riesgo - Año {year}', fontsize=16, pad=20)
                ax.set_xlabel('Cluster Incendio Individual', fontsize=14)
                ax.set_ylabel('Cluster Regional', fontsize=14)
            
            fig.tight_layout()
            self.canvases["matrix"]["canvas"].draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar matriz de riesgo: {str(e)}")
    
    def update_summary_data(self):
        try:
            year = self.current_year.get()
            
            # Top 10 regions
            top10 = model_backend.get_top10_regions_by_year(self.df, year)
            self.top10_text.delete(1.0, tk.END)
            self.top10_text.insert(tk.END, f"TOP 10 REGIONES - AÑO {year}\n\n")
            self.top10_text.insert(tk.END, top10[['Latitud_round', 'Longitud_round', 'frecuencia_incendios', 'vegetacion_predominante']].to_string(index=False))
            
            # Ecosystem summary
            eco = model_backend.get_ecosystem_summary_by_year(self.df, year)
            self.eco_text.delete(1.0, tk.END)
            self.eco_text.insert(tk.END, f"RESUMEN DE ECOSISTEMAS - AÑO {year}\n\n")
            self.eco_text.insert(tk.END, eco.to_string(index=False))
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar datos de resumen: {str(e)}")
    
    def show_historical_analysis(self):
        try:
            results = model_backend.historical_analysis('BD.csv')
            
            # Create a new window
            hist_window = tk.Toplevel(self.root)
            hist_window.title("Análisis Histórico (2015-2023)")
            hist_window.geometry("1000x700")
            
            # Create notebook for tabs
            notebook = ttk.Notebook(hist_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Regional clusters tab with scrollbar
            regional_tab = ttk.Frame(notebook)
            notebook.add(regional_tab, text="Clusters Regionales")
            
            # Crear un panel horizontal para la leyenda y el gráfico
            regional_panel = ttk.PanedWindow(regional_tab, orient=tk.HORIZONTAL)
            regional_panel.pack(fill=tk.BOTH, expand=True)
            
            # Panel izquierdo para la leyenda con scroll
            regional_legend_panel = ttk.Frame(regional_panel, width=200)
            regional_panel.add(regional_legend_panel, weight=1)
            
            # Crear canvas con scrollbar para la leyenda
            regional_legend_canvas = tk.Canvas(regional_legend_panel)
            regional_legend_scrollbar = ttk.Scrollbar(regional_legend_panel, orient="vertical", command=regional_legend_canvas.yview)
            regional_legend_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            regional_legend_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            regional_legend_canvas.configure(yscrollcommand=regional_legend_scrollbar.set)
            
            regional_legend_content = ttk.Frame(regional_legend_canvas)
            regional_legend_canvas.create_window((0, 0), window=regional_legend_content, anchor="nw")
            
            # Panel derecho para el gráfico con scroll
            regional_graph_panel = ttk.Frame(regional_panel)
            regional_panel.add(regional_graph_panel, weight=4)
            
            regional_canvas = tk.Canvas(regional_graph_panel)
            regional_scrollbar = ttk.Scrollbar(regional_graph_panel, orient="vertical", command=regional_canvas.yview)
            regional_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            regional_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            # CORRECCIÓN: Eliminamos 'fill' y 'expand' de configure
            regional_canvas.configure(yscrollcommand=regional_scrollbar.set)
            
            regional_content = ttk.Frame(regional_canvas)
            regional_canvas.create_window((0, 0), window=regional_content, anchor="nw")
            
            # Crear figura con tamaño fijo
            fig1_frame = ttk.Frame(regional_content, width=900, height=600)
            fig1_frame.pack(padx=10, pady=10)
            fig1_frame.pack_propagate(False)
            
            fig1 = Figure(figsize=(9, 6), dpi=100)
            ax1 = fig1.add_subplot(111)
            
            # Crear el scatter plot sin leyenda en el gráfico
            scatter = sns.scatterplot(
                x='Longitud_round', y='Latitud_round', 
                hue='cluster_region', size='frecuencia_incendios', 
                sizes=(20, 200), palette='viridis', 
                data=results['regional'], alpha=0.7, ax=ax1,
                legend=False
            )
            
            ax1.set_title('Clusters Regionales Históricos (2015-2023)', fontsize=16, pad=20)
            ax1.set_xlabel('Longitud', fontsize=14)
            ax1.set_ylabel('Latitud', fontsize=14)
            ax1.set_aspect('equal')
            
            fig1.tight_layout()
            
            canvas1 = FigureCanvasTkAgg(fig1, master=fig1_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Crear leyenda en el panel izquierdo
            ttk.Label(regional_legend_content, text="Clusters Regionales", font=("Arial", 12, "bold")).pack(pady=5)
            
            # Crear leyenda para clusters regionales
            unique_clusters = results['regional']['cluster_region'].unique()
            colors = plt.cm.viridis(np.linspace(0, 1, len(unique_clusters)))
            
            for i, cluster in enumerate(sorted(unique_clusters)):
                cluster_frame = ttk.Frame(regional_legend_content)
                cluster_frame.pack(fill=tk.X, pady=2)
                
                # Crear un cuadrado de color para el cluster
                color_canvas = tk.Canvas(cluster_frame, width=15, height=15, bg=self.rgb_to_hex(colors[i][:3]))
                color_canvas.pack(side=tk.LEFT, padx=5)
                
                # Etiqueta con el número de cluster
                ttk.Label(cluster_frame, text=f"Cluster {cluster}").pack(side=tk.LEFT, padx=5)
            
            # Leyenda para tamaño de puntos
            ttk.Label(regional_legend_content, text="Frecuencia de Incendios", font=("Arial", 10, "bold")).pack(pady=5)
            
            # Mostrar rangos de frecuencia
            freq_ranges = [(15, "Baja"), (45, "Media"), (75, "Alta")]
            for size, label in freq_ranges:
                size_frame = ttk.Frame(regional_legend_content)
                size_frame.pack(fill=tk.X, pady=2)
                
                # Crear un círculo proporcional al tamaño
                size_canvas = tk.Canvas(size_frame, width=30, height=20)
                size_canvas.pack(side=tk.LEFT, padx=5)
                radius = min(size / 3, 8)
                size_canvas.create_oval(15-radius, 10-radius, 15+radius, 10+radius, fill="gray")
                
                # Etiqueta con el rango
                ttk.Label(size_frame, text=f"{label} ({size})").pack(side=tk.LEFT, padx=5)
            
            regional_legend_content.bind("<Configure>", lambda e: regional_legend_canvas.configure(scrollregion=regional_legend_canvas.bbox("all")))
            regional_content.bind("<Configure>", lambda e: regional_canvas.configure(scrollregion=regional_canvas.bbox("all")))
            
            # Individual clusters tab
            individual_tab = ttk.Frame(notebook)
            notebook.add(individual_tab, text="Clusters Individuales")
            
            individual_panel = ttk.PanedWindow(individual_tab, orient=tk.HORIZONTAL)
            individual_panel.pack(fill=tk.BOTH, expand=True)
            
            individual_legend_panel = ttk.Frame(individual_panel, width=200)
            individual_panel.add(individual_legend_panel, weight=1)
            
            individual_legend_canvas = tk.Canvas(individual_legend_panel)
            individual_legend_scrollbar = ttk.Scrollbar(individual_legend_panel, orient="vertical", command=individual_legend_canvas.yview)
            individual_legend_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            individual_legend_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            individual_legend_canvas.configure(yscrollcommand=individual_legend_scrollbar.set)
            
            individual_legend_content = ttk.Frame(individual_legend_canvas)
            individual_legend_canvas.create_window((0, 0), window=individual_legend_content, anchor="nw")
            
            individual_graph_panel = ttk.Frame(individual_panel)
            individual_panel.add(individual_graph_panel, weight=4)
            
            individual_canvas = tk.Canvas(individual_graph_panel)
            individual_scrollbar = ttk.Scrollbar(individual_graph_panel, orient="vertical", command=individual_canvas.yview)
            individual_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            individual_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            individual_canvas.configure(yscrollcommand=individual_scrollbar.set)
            
            individual_content = ttk.Frame(individual_canvas)
            individual_canvas.create_window((0, 0), window=individual_content, anchor="nw")
            
            fig2_frame = ttk.Frame(individual_content, width=900, height=600)
            fig2_frame.pack(padx=10, pady=10)
            fig2_frame.pack_propagate(False)
            
            fig2 = Figure(figsize=(9, 6), dpi=100)
            ax2 = fig2.add_subplot(111)
            
            ind_summary = results['individual']['summary']
            sns.barplot(
                x='cluster_incendio', y='num_incendios', 
                data=ind_summary, ax=ax2, palette='plasma',
                legend=False
            )
            
            ax2.set_title('Clusters Individuales Históricos (2015-2023)', fontsize=16, pad=20)
            ax2.set_xlabel('Cluster Incendio', fontsize=14)
            ax2.set_ylabel('Número de Incendios', fontsize=14)
            for i, v in enumerate(ind_summary['num_incendios']):
                ax2.text(i, v + 5, str(v), ha='center', fontsize=12)
            
            fig2.tight_layout()
            
            canvas2 = FigureCanvasTkAgg(fig2, master=fig2_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(individual_legend_content, text="Clusters Individuales", font=("Arial", 12, "bold")).pack(pady=5)
            unique_clusters = ind_summary['cluster_incendio'].unique()
            colors = plt.cm.plasma(np.linspace(0, 1, len(unique_clusters)))
            
            for i, cluster in enumerate(sorted(unique_clusters)):
                cluster_frame = ttk.Frame(individual_legend_content)
                cluster_frame.pack(fill=tk.X, pady=2)
                color_canvas = tk.Canvas(cluster_frame, width=15, height=15, bg=self.rgb_to_hex(colors[i][:3]))
                color_canvas.pack(side=tk.LEFT, padx=5)
                ttk.Label(cluster_frame, text=f"Cluster {cluster}").pack(side=tk.LEFT, padx=5)
            
            individual_legend_content.bind("<Configure>", lambda e: individual_legend_canvas.configure(scrollregion=individual_legend_canvas.bbox("all")))
            individual_content.bind("<Configure>", lambda e: individual_canvas.configure(scrollregion=individual_canvas.bbox("all")))
            
            # Timeline tab
            timeline_tab = ttk.Frame(notebook)
            notebook.add(timeline_tab, text="Línea de Tiempo")
            
            timeline_canvas = tk.Canvas(timeline_tab)
            timeline_scrollbar = ttk.Scrollbar(timeline_tab, orient="vertical", command=timeline_canvas.yview)
            timeline_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            timeline_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            timeline_canvas.configure(yscrollcommand=timeline_scrollbar.set)
            
            timeline_content = ttk.Frame(timeline_canvas)
            timeline_canvas.create_window((0, 0), window=timeline_content, anchor="nw")
            
            fig3_frame = ttk.Frame(timeline_content, width=900, height=600)
            fig3_frame.pack(padx=10, pady=10)
            fig3_frame.pack_propagate(False)
            
            fig3 = Figure(figsize=(9, 6), dpi=100)
            ax3 = fig3.add_subplot(111)
            
            yearly_counts = self.df.groupby('Año').size().reset_index(name='Incendios')
            sns.lineplot(
                x='Año', y='Incendios', 
                data=yearly_counts, marker='o', 
                linewidth=2, markersize=10, ax=ax3,
                color='#1f77b4'
            )
            
            ax3.set_title('Evolución de Incendios por Año (2015-2023)', fontsize=16, pad=20)
            ax3.set_xlabel('Año', fontsize=14)
            ax3.set_ylabel('Número de Incendios', fontsize=14)
            ax3.grid(True, linestyle='--', alpha=0.7)
            for x, y in zip(yearly_counts['Año'], yearly_counts['Incendios']):
                ax3.text(x, y + 5, str(y), ha='center', fontsize=12)
            
            fig3.tight_layout()
            
            canvas3 = FigureCanvasTkAgg(fig3, master=fig3_frame)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            timeline_content.bind("<Configure>", lambda e: timeline_canvas.configure(scrollregion=timeline_canvas.bbox("all")))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en el análisis histórico: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_historical_risk_matrix(self):
        try:
            risk_matrix = model_backend.compute_risk_matrix_historical('BD.csv')
            
            matrix_window = tk.Toplevel(self.root)
            matrix_window.title("Matriz de Riesgo Histórica (2015-2023)")
            matrix_window.geometry("800x600")
            
            matrix_canvas = tk.Canvas(matrix_window)
            matrix_scrollbar = ttk.Scrollbar(matrix_window, orient="vertical", command=matrix_canvas.yview)
            matrix_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            matrix_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            matrix_canvas.configure(yscrollcommand=matrix_scrollbar.set)
            
            matrix_content = ttk.Frame(matrix_canvas)
            matrix_canvas.create_window((0, 0), window=matrix_content, anchor="nw")
            
            fig_frame = ttk.Frame(matrix_content, width=700, height=600)
            fig_frame.pack(padx=10, pady=10)
            fig_frame.pack_propagate(False)
            
            fig = Figure(figsize=(7, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            sns.heatmap(
                risk_matrix, annot=True, fmt='g', 
                cmap='YlOrRd', ax=ax,
                cbar_kws={'label': 'Nivel de Riesgo'},
                annot_kws={"size": 12}
            )
            
            ax.set_title('Matriz de Riesgo Histórica (2015-2023)', fontsize=16, pad=20)
            ax.set_xlabel('Cluster Incendio Individual', fontsize=14)
            ax.set_ylabel('Cluster Regional', fontsize=14)
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=fig_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            matrix_content.bind("<Configure>", lambda e: matrix_canvas.configure(scrollregion=matrix_canvas.bbox("all")))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar Matriz de Riesgo Histórica: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_historical_summary(self):
        try:
            summary_window = tk.Toplevel(self.root)
            summary_window.title("Resumen Histórico (2015-2023)")
            summary_window.geometry("1000x600")
            
            notebook = ttk.Notebook(summary_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            top10_tab = ttk.Frame(notebook)
            notebook.add(top10_tab, text="Top 10 Regiones")
            
            top10 = model_backend.get_top10_regions_historical('BD.csv')
            
            top10_text = scrolledtext.ScrolledText(top10_tab, width=80, height=20)
            top10_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            top10_text.insert(tk.END, "TOP 10 REGIONES HISTÓRICAS (2015-2023)\n\n")
            top10_text.insert(tk.END, top10[['Latitud_round', 'Longitud_round', 'frecuencia_incendios', 'vegetacion_predominante']].to_string(index=False))
            
            eco_tab = ttk.Frame(notebook)
            notebook.add(eco_tab, text="Resumen Ecosistemas")
            
            eco = model_backend.get_ecosystem_summary_historical('BD.csv')
            
            eco_text = scrolledtext.ScrolledText(eco_tab, width=80, height=20)
            eco_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            eco_text.insert(tk.END, "RESUMEN DE ECOSISTEMAS HISTÓRICOS (2015-2023)\n\n")
            eco_text.insert(tk.END, eco.to_string(index=False))
            
            comparison_tab = ttk.Frame(notebook)
            notebook.add(comparison_tab, text="Comparativa Anual")
            
            comparison_canvas = tk.Canvas(comparison_tab)
            comparison_scrollbar = ttk.Scrollbar(comparison_tab, orient="vertical", command=comparison_canvas.yview)
            comparison_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            comparison_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            comparison_canvas.configure(yscrollcommand=comparison_scrollbar.set)
            
            comparison_content = ttk.Frame(comparison_canvas)
            comparison_canvas.create_window((0, 0), window=comparison_content, anchor="nw")
            
            fig_frame = ttk.Frame(comparison_content, width=900, height=600)
            fig_frame.pack(padx=10, pady=10)
            fig_frame.pack_propagate(False)
            
            fig = Figure(figsize=(9, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            eco_yearly = self.df.groupby(['Año', 'Ecosistema']).size().reset_index(name='Incendios')
            eco_pivot = eco_yearly.pivot(index='Año', columns='Ecosistema', values='Incendios').fillna(0)
            
            eco_pivot.plot(kind='bar', stacked=True, ax=ax, colormap='viridis')
            
            ax.set_title('Incendios por Ecosistema y Año (2015-2023)', fontsize=16, pad=20)
            ax.set_xlabel('Año', fontsize=14)
            ax.set_ylabel('Número de Incendios', fontsize=14)
            ax.legend(title='Ecosistema', loc='upper right', fontsize=10, title_fontsize=12)
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=fig_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            comparison_content.bind("<Configure>", lambda e: comparison_canvas.configure(scrollregion=comparison_canvas.bbox("all")))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar Resumen Histórico: {str(e)}")
            import traceback
            traceback.print_exc()

# Función para probar la aplicación de forma independiente
def fix_matplotlib_for_tkinter():
    """
    Solución para problemas de visualización de matplotlib en Tkinter
    """
    import matplotlib
    matplotlib.use('TkAgg')  # Usar el backend TkAgg
    
    # Configurar para que las figuras se rendericen correctamente
    plt.rcParams['figure.autolayout'] = True
    plt.rcParams['figure.figsize'] = [10, 6]
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['font.size'] = 12
    plt.rcParams['legend.fontsize'] = 10
    plt.rcParams['figure.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12

if __name__ == "__main__":
    fix_matplotlib_for_tkinter()
    
    root = tk.Tk()
    app = WildfireAnalysisApp(root)
    root.mainloop()
