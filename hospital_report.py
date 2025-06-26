#!/usr/bin/env python3
"""
Generador de Informes Final Optimizado de Capacidad Hospitalaria
Secretaría de Salud del Tolima - Estructura por Servicios

Versión actualizada con enfoque por tipos de servicio:
- Observación/Urgencias: Camas y camillas de observación
- Cuidado Crítico: UCI y Cuidado Intermedio
- Hospitalización: Adulto, Pediátrica, etc.

Estructura del informe: Tolima → Ibagué → Demás Municipios

Desarrollado por: Ing. José Miguel Santos
Para: Secretaría de Salud del Tolima
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import sys
import os
from pathlib import Path
import warnings
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import matplotlib.patches as mpatches

# Configurar warnings
warnings.filterwarnings('ignore')

# Configuración de matplotlib
plt.style.use('default')
sns.set_palette("husl")

# Configuración global
COLORS = {
    "primary": "#7D0F2B",     # Rojo institucional Tolima
    "secondary": "#F2A900",    # Amarillo dorado
    "accent": "#5A4214",       # Marrón
    "success": "#509E2F",      # Verde
    "warning": "#F7941D",      # Naranja
    "danger": "#D32F2F",       # Rojo peligro
    "white": "#FFFFFF",        # Blanco
    "light_gray": "#F5F5F5",   # Gris claro
    "dark_gray": "#424242",    # Gris oscuro
}

# Umbrales de ocupación
UMBRALES = {
    "critico": 90,      # ≥90% crítico
    "advertencia": 70,  # 70-89% advertencia
    "normal": 0         # <70% normal
}

class HospitalReportGenerator:
    """Generador de informes de capacidad hospitalaria optimizado por servicios."""
    
    def __init__(self):
        """Inicializar el generador de reportes."""
        self.df = None
        self.fecha_procesamiento = datetime.now()
        self.mapeo_servicios = self._crear_mapeo_servicios()
        
    def _crear_mapeo_servicios(self):
        """Crear mapeo de capacidades a tipos de servicio."""
        return {
            'observacion': {
                'nombre': 'Observación/Urgencias',
                'descripcion': 'Servicios de urgencias y observación',
                'keywords': ['observacion', 'urgencias', 'emergencia'],
                'color': COLORS['warning']
            },
            'cuidado_critico': {
                'nombre': 'Cuidado Crítico',
                'descripcion': 'UCI y Cuidado Intermedio',
                'keywords': ['uci', 'cuidado intensivo', 'cuidado intermedio', 'intensivo', 'intermedio'],
                'color': COLORS['danger']
            },
            'hospitalizacion': {
                'nombre': 'Hospitalización',
                'descripcion': 'Servicios de hospitalización general',
                'keywords': ['adulto', 'pediatric', 'gineco', 'medicina', 'cirugia', 'general'],
                'color': COLORS['primary']
            }
        }
    
    def _clasificar_servicio(self, nombre_capacidad):
        """Clasificar una capacidad en tipo de servicio."""
        nombre_lower = str(nombre_capacidad).lower()
        
        # Verificar observación/urgencias
        for keyword in self.mapeo_servicios['observacion']['keywords']:
            if keyword in nombre_lower:
                return 'observacion'
        
        # Verificar cuidado crítico
        for keyword in self.mapeo_servicios['cuidado_critico']['keywords']:
            if keyword in nombre_lower:
                return 'cuidado_critico'
        
        # Por defecto, hospitalización
        return 'hospitalizacion'
    
    def cargar_datos(self, archivo_excel):
        """Cargar y procesar datos del archivo Excel."""
        try:
            print(f"📂 Cargando datos desde: {archivo_excel}")
            
            # Cargar datos
            self.df = pd.read_excel(archivo_excel)
            print(f"📊 Datos cargados: {len(self.df)} registros")
            
            # Procesar datos
            self._procesar_datos()
            print("✅ Datos procesados exitosamente")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar datos: {str(e)}")
            return False
    
    def _procesar_datos(self):
        """Procesar y limpiar los datos cargados."""
        # Limpiar nombres de columnas
        self.df.columns = self.df.columns.str.strip()
        
        # Convertir valores numéricos
        columnas_numericas = [
            'cantidad_ci_TOTAL_REPS',
            'ocupacion_ci_confirmado_covid19', 
            'ocupacion_ci_sospechoso_covid19',
            'ocupacion_ci_no_covid19',
            'cantidad_ci_disponibles',
            'total_ingresos_paciente_servicio'
        ]
        
        for col in columnas_numericas:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # Calcular ocupación total
        self.df['ocupacion_total'] = (
            self.df['ocupacion_ci_confirmado_covid19'] + 
            self.df['ocupacion_ci_sospechoso_covid19'] + 
            self.df['ocupacion_ci_no_covid19']
        )
        
        # Calcular porcentaje de ocupación
        self.df['porcentaje_ocupacion'] = np.where(
            self.df['cantidad_ci_TOTAL_REPS'] > 0,
            (self.df['ocupacion_total'] / self.df['cantidad_ci_TOTAL_REPS']) * 100,
            0
        )
        
        # Clasificar por tipo de servicio
        self.df['tipo_servicio'] = self.df['nombre_capacidad_instalada'].apply(self._clasificar_servicio)
        
        # Limpiar nombres de municipios
        self.df['municipio_sede_prestador'] = self.df['municipio_sede_prestador'].str.strip().str.title()
        
        # Asegurar que Ibagué esté bien escrito
        self.df['municipio_sede_prestador'] = self.df['municipio_sede_prestador'].replace(
            ['Ibague', 'IBAGUE', 'ibague'], 'Ibagué'
        )
    
    def _obtener_estadisticas_tolima(self):
        """Obtener estadísticas generales del departamento del Tolima."""
        stats = {}
        
        # Totales por tipo de servicio
        for tipo_servicio in self.mapeo_servicios.keys():
            df_servicio = self.df[self.df['tipo_servicio'] == tipo_servicio]
            
            stats[tipo_servicio] = {
                'capacidad_total': df_servicio['cantidad_ci_TOTAL_REPS'].sum(),
                'ocupacion_total': df_servicio['ocupacion_total'].sum(),
                'ocupacion_covid': df_servicio['ocupacion_ci_confirmado_covid19'].sum() + 
                                 df_servicio['ocupacion_ci_sospechoso_covid19'].sum(),
                'ocupacion_no_covid': df_servicio['ocupacion_ci_no_covid19'].sum(),
                'disponible': df_servicio['cantidad_ci_disponibles'].sum()
            }
            
            # Calcular porcentajes
            if stats[tipo_servicio]['capacidad_total'] > 0:
                stats[tipo_servicio]['porcentaje_ocupacion'] = (
                    stats[tipo_servicio]['ocupacion_total'] / 
                    stats[tipo_servicio]['capacidad_total']
                ) * 100
            else:
                stats[tipo_servicio]['porcentaje_ocupacion'] = 0
        
        # Estadísticas generales
        stats['general'] = {
            'total_municipios': self.df['municipio_sede_prestador'].nunique(),
            'total_prestadores': self.df['nombre_prestador'].nunique(),
            'total_sedes': self.df['nombre_sede_prestador'].nunique(),
            'capacidad_total_departamento': self.df['cantidad_ci_TOTAL_REPS'].sum(),
            'ocupacion_total_departamento': self.df['ocupacion_total'].sum(),
            'porcentaje_ocupacion_departamento': (
                self.df['ocupacion_total'].sum() / self.df['cantidad_ci_TOTAL_REPS'].sum() * 100
                if self.df['cantidad_ci_TOTAL_REPS'].sum() > 0 else 0
            )
        }
        
        return stats
    
    def _obtener_estadisticas_ibague(self):
        """Obtener estadísticas específicas de Ibagué."""
        df_ibague = self.df[self.df['municipio_sede_prestador'] == 'Ibagué']
        
        if df_ibague.empty:
            return None
        
        stats = {}
        
        # Por tipo de servicio
        for tipo_servicio in self.mapeo_servicios.keys():
            df_servicio = df_ibague[df_ibague['tipo_servicio'] == tipo_servicio]
            
            stats[tipo_servicio] = {
                'capacidad_total': df_servicio['cantidad_ci_TOTAL_REPS'].sum(),
                'ocupacion_total': df_servicio['ocupacion_total'].sum(),
                'ocupacion_covid': df_servicio['ocupacion_ci_confirmado_covid19'].sum() + 
                                 df_servicio['ocupacion_ci_sospechoso_covid19'].sum(),
                'ocupacion_no_covid': df_servicio['ocupacion_ci_no_covid19'].sum(),
                'disponible': df_servicio['cantidad_ci_disponibles'].sum(),
                'prestadores': df_servicio['nombre_prestador'].nunique(),
                'sedes': df_servicio['nombre_sede_prestador'].nunique()
            }
            
            if stats[tipo_servicio]['capacidad_total'] > 0:
                stats[tipo_servicio]['porcentaje_ocupacion'] = (
                    stats[tipo_servicio]['ocupacion_total'] / 
                    stats[tipo_servicio]['capacidad_total']
                ) * 100
            else:
                stats[tipo_servicio]['porcentaje_ocupacion'] = 0
        
        return stats
    
    def _obtener_estadisticas_otros_municipios(self):
        """Obtener estadísticas de municipios diferentes a Ibagué."""
        df_otros = self.df[self.df['municipio_sede_prestador'] != 'Ibagué']
        
        if df_otros.empty:
            return None
        
        # Agrupar por municipio y tipo de servicio
        stats_municipios = []
        
        for municipio in df_otros['municipio_sede_prestador'].unique():
            df_municipio = df_otros[df_otros['municipio_sede_prestador'] == municipio]
            
            municipio_stats = {
                'municipio': municipio,
                'prestadores': df_municipio['nombre_prestador'].nunique(),
                'sedes': df_municipio['nombre_sede_prestador'].nunique()
            }
            
            # Por tipo de servicio
            for tipo_servicio in self.mapeo_servicios.keys():
                df_servicio = df_municipio[df_municipio['tipo_servicio'] == tipo_servicio]
                
                capacidad = df_servicio['cantidad_ci_TOTAL_REPS'].sum()
                ocupacion = df_servicio['ocupacion_total'].sum()
                
                municipio_stats[f'{tipo_servicio}_capacidad'] = capacidad
                municipio_stats[f'{tipo_servicio}_ocupacion'] = ocupacion
                municipio_stats[f'{tipo_servicio}_porcentaje'] = (
                    (ocupacion / capacidad * 100) if capacidad > 0 else 0
                )
            
            # Totales del municipio
            municipio_stats['total_capacidad'] = df_municipio['cantidad_ci_TOTAL_REPS'].sum()
            municipio_stats['total_ocupacion'] = df_municipio['ocupacion_total'].sum()
            municipio_stats['total_porcentaje'] = (
                (municipio_stats['total_ocupacion'] / municipio_stats['total_capacidad'] * 100)
                if municipio_stats['total_capacidad'] > 0 else 0
            )
            
            stats_municipios.append(municipio_stats)
        
        return sorted(stats_municipios, key=lambda x: x['total_capacidad'], reverse=True)
    
    def _crear_grafico_tolima_servicios(self):
        """Crear gráfico de servicios del departamento del Tolima."""
        try:
            stats = self._obtener_estadisticas_tolima()
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            fig.suptitle('Capacidad y Ocupación Hospitalaria por Servicios - Departamento del Tolima', 
                        fontsize=16, fontweight='bold', color=COLORS['primary'])
            
            # Datos para gráficos
            servicios = []
            capacidades = []
            ocupaciones = []
            porcentajes = []
            colores = []
            
            for tipo_servicio, info in self.mapeo_servicios.items():
                if tipo_servicio in stats:
                    servicios.append(info['nombre'])
                    capacidades.append(stats[tipo_servicio]['capacidad_total'])
                    ocupaciones.append(stats[tipo_servicio]['ocupacion_total'])
                    porcentajes.append(stats[tipo_servicio]['porcentaje_ocupacion'])
                    colores.append(info['color'])
            
            # Gráfico 1: Capacidad vs Ocupación
            x = np.arange(len(servicios))
            width = 0.35
            
            bars1 = ax1.bar(x - width/2, capacidades, width, label='Capacidad Total', 
                          color=colores, alpha=0.7)
            bars2 = ax1.bar(x + width/2, ocupaciones, width, label='Ocupación Actual', 
                          color=colores, alpha=1.0)
            
            ax1.set_title('Capacidad vs Ocupación por Servicio', fontweight='bold')
            ax1.set_ylabel('Número de Unidades')
            ax1.set_xlabel('Tipo de Servicio')
            ax1.set_xticks(x)
            ax1.set_xticklabels(servicios, rotation=45, ha='right')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Agregar valores en las barras
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 5,
                           f'{int(height)}', ha='center', va='bottom', fontweight='bold')
            
            for bar in bars2:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 5,
                           f'{int(height)}', ha='center', va='bottom', fontweight='bold')
            
            # Gráfico 2: Porcentajes de Ocupación
            bars3 = ax2.bar(servicios, porcentajes, color=colores, alpha=0.8)
            
            ax2.set_title('Porcentaje de Ocupación por Servicio', fontweight='bold')
            ax2.set_ylabel('Porcentaje de Ocupación (%)')
            ax2.set_xlabel('Tipo de Servicio')
            ax2.set_xticklabels(servicios, rotation=45, ha='right')
            
            # Líneas de referencia
            ax2.axhline(y=UMBRALES['advertencia'], color='orange', linestyle='--', alpha=0.7, label='Advertencia (70%)')
            ax2.axhline(y=UMBRALES['critico'], color='red', linestyle='--', alpha=0.7, label='Crítico (90%)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Agregar valores en las barras
            for i, (bar, porcentaje) in enumerate(zip(bars3, porcentajes)):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{porcentaje:.1f}%', ha='center', va='bottom', fontweight='bold')
                
                # Colorear según umbral
                if porcentaje >= UMBRALES['critico']:
                    bar.set_edgecolor('red')
                    bar.set_linewidth(3)
                elif porcentaje >= UMBRALES['advertencia']:
                    bar.set_edgecolor('orange')
                    bar.set_linewidth(2)
            
            plt.tight_layout()
            plt.savefig('grafico_tolima_servicios.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            return 'grafico_tolima_servicios.png'
            
        except Exception as e:
            print(f"❌ Error creando gráfico de Tolima: {str(e)}")
            return None
    
    def _crear_grafico_ibague_detallado(self):
        """Crear gráfico detallado específico de Ibagué."""
        try:
            stats = self._obtener_estadisticas_ibague()
            if not stats:
                return None
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Análisis Detallado de Capacidad Hospitalaria - Ibagué', 
                        fontsize=16, fontweight='bold', color=COLORS['primary'])
            
            # Datos para gráficos
            servicios = []
            capacidades = []
            ocupaciones = []
            porcentajes = []
            colores = []
            
            for tipo_servicio, info in self.mapeo_servicios.items():
                if tipo_servicio in stats:
                    servicios.append(info['nombre'])
                    capacidades.append(stats[tipo_servicio]['capacidad_total'])
                    ocupaciones.append(stats[tipo_servicio]['ocupacion_total'])
                    porcentajes.append(stats[tipo_servicio]['porcentaje_ocupacion'])
                    colores.append(info['color'])
            
            # Gráfico 1: Capacidad vs Ocupación
            x = np.arange(len(servicios))
            width = 0.35
            
            bars1 = ax1.bar(x - width/2, capacidades, width, label='Capacidad', 
                          color=colores, alpha=0.7)
            bars2 = ax1.bar(x + width/2, ocupaciones, width, label='Ocupación', 
                          color=colores, alpha=1.0)
            
            ax1.set_title('Capacidad vs Ocupación', fontweight='bold')
            ax1.set_ylabel('Número de Unidades')
            ax1.set_xticks(x)
            ax1.set_xticklabels(servicios, rotation=45, ha='right')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Valores en barras
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 5,
                           f'{int(height)}', ha='center', va='bottom', fontsize=10)
            
            for bar in bars2:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 5,
                           f'{int(height)}', ha='center', va='bottom', fontsize=10)
            
            # Gráfico 2: Porcentajes de Ocupación
            bars3 = ax2.bar(servicios, porcentajes, color=colores, alpha=0.8)
            ax2.set_title('Porcentaje de Ocupación', fontweight='bold')
            ax2.set_ylabel('Porcentaje (%)')
            ax2.set_xticklabels(servicios, rotation=45, ha='right')
            ax2.axhline(y=70, color='orange', linestyle='--', alpha=0.7)
            ax2.axhline(y=90, color='red', linestyle='--', alpha=0.7)
            ax2.grid(True, alpha=0.3)
            
            for bar, porcentaje in zip(bars3, porcentajes):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{porcentaje:.1f}%', ha='center', va='bottom', fontsize=10)
            
            # Gráfico 3: Distribución COVID vs No COVID
            df_ibague = self.df[self.df['municipio_sede_prestador'] == 'Ibagué']
            
            covid_data = []
            no_covid_data = []
            
            for tipo_servicio in self.mapeo_servicios.keys():
                df_servicio = df_ibague[df_ibague['tipo_servicio'] == tipo_servicio]
                covid_data.append(stats[tipo_servicio]['ocupacion_covid'])
                no_covid_data.append(stats[tipo_servicio]['ocupacion_no_covid'])
            
            x = np.arange(len(servicios))
            width = 0.35
            
            ax3.bar(x - width/2, covid_data, width, label='COVID-19', color='red', alpha=0.7)
            ax3.bar(x + width/2, no_covid_data, width, label='No COVID-19', color='blue', alpha=0.7)
            
            ax3.set_title('Ocupación: COVID-19 vs No COVID-19', fontweight='bold')
            ax3.set_ylabel('Pacientes')
            ax3.set_xticks(x)
            ax3.set_xticklabels(servicios, rotation=45, ha='right')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # Gráfico 4: Prestadores por Servicio
            prestadores_data = [stats[tipo]['prestadores'] for tipo in self.mapeo_servicios.keys()]
            
            ax4.bar(servicios, prestadores_data, color=colores, alpha=0.8)
            ax4.set_title('Número de Prestadores por Servicio', fontweight='bold')
            ax4.set_ylabel('Número de Prestadores')
            ax4.set_xticklabels(servicios, rotation=45, ha='right')
            ax4.grid(True, alpha=0.3)
            
            for i, v in enumerate(prestadores_data):
                ax4.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            plt.savefig('grafico_ibague_detallado.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            return 'grafico_ibague_detallado.png'
            
        except Exception as e:
            print(f"❌ Error creando gráfico de Ibagué: {str(e)}")
            return None
    
    def _crear_grafico_otros_municipios(self):
        """Crear gráfico de otros municipios (excluyendo Ibagué)."""
        try:
            stats_municipios = self._obtener_estadisticas_otros_municipios()
            if not stats_municipios:
                return None
            
            # Tomar los 15 municipios con mayor capacidad
            top_municipios = stats_municipios[:15]
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
            fig.suptitle('Capacidad Hospitalaria - Otros Municipios del Tolima (Top 15)', 
                        fontsize=16, fontweight='bold', color=COLORS['primary'])
            
            municipios = [m['municipio'] for m in top_municipios]
            capacidades = [m['total_capacidad'] for m in top_municipios]
            ocupaciones = [m['total_ocupacion'] for m in top_municipios]
            porcentajes = [m['total_porcentaje'] for m in top_municipios]
            
            # Gráfico 1: Capacidad vs Ocupación
            x = np.arange(len(municipios))
            width = 0.35
            
            bars1 = ax1.bar(x - width/2, capacidades, width, label='Capacidad Total', 
                          color=COLORS['secondary'], alpha=0.7)
            bars2 = ax1.bar(x + width/2, ocupaciones, width, label='Ocupación Actual', 
                          color=COLORS['primary'], alpha=0.8)
            
            ax1.set_title('Capacidad vs Ocupación por Municipio', fontweight='bold')
            ax1.set_ylabel('Número de Unidades')
            ax1.set_xlabel('Municipio')
            ax1.set_xticks(x)
            ax1.set_xticklabels(municipios, rotation=45, ha='right')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Valores en barras
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                           f'{int(height)}', ha='center', va='bottom', fontsize=8)
            
            # Gráfico 2: Porcentajes de Ocupación
            bars3 = ax2.bar(municipios, porcentajes, alpha=0.8)
            
            # Colorear según umbrales
            for i, (bar, porcentaje) in enumerate(zip(bars3, porcentajes)):
                if porcentaje >= UMBRALES['critico']:
                    bar.set_color(COLORS['danger'])
                elif porcentaje >= UMBRALES['advertencia']:
                    bar.set_color(COLORS['warning'])
                else:
                    bar.set_color(COLORS['success'])
                
                # Agregar valor
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                       f'{porcentaje:.1f}%', ha='center', va='bottom', fontsize=8)
            
            ax2.set_title('Porcentaje de Ocupación por Municipio', fontweight='bold')
            ax2.set_ylabel('Porcentaje de Ocupación (%)')
            ax2.set_xlabel('Municipio')
            ax2.set_xticklabels(municipios, rotation=45, ha='right')
            
            # Líneas de referencia
            ax2.axhline(y=UMBRALES['advertencia'], color='orange', linestyle='--', alpha=0.7, label='Advertencia (70%)')
            ax2.axhline(y=UMBRALES['critico'], color='red', linestyle='--', alpha=0.7, label='Crítico (90%)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('grafico_otros_municipios.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            return 'grafico_otros_municipios.png'
            
        except Exception as e:
            print(f"❌ Error creando gráfico de otros municipios: {str(e)}")
            return None
    
    def _crear_tabla_detallada_ibague(self):
        """Crear tabla detallada de Ibagué por prestador y servicio."""
        df_ibague = self.df[self.df['municipio_sede_prestador'] == 'Ibagué']
        
        if df_ibague.empty:
            return None
        
        tabla_data = []
        
        # Encabezados
        headers = [
            'Prestador/Sede',
            'Observación\nCap./Ocup./(%)',
            'Cuidado Crítico\nCap./Ocup./(%)',
            'Hospitalización\nCap./Ocup./(%)',
            'Total\nCap./Ocup./(%)'
        ]
        
        # Datos por prestador
        for prestador in df_ibague['nombre_prestador'].unique():
            df_prestador = df_ibague[df_ibague['nombre_prestador'] == prestador]
            
            # Fila del prestador (totales)
            prestador_row = [f"📋 {prestador}"]
            
            total_cap = 0
            total_ocup = 0
            
            for tipo_servicio in ['observacion', 'cuidado_critico', 'hospitalizacion']:
                df_servicio = df_prestador[df_prestador['tipo_servicio'] == tipo_servicio]
                cap = df_servicio['cantidad_ci_TOTAL_REPS'].sum()
                ocup = df_servicio['ocupacion_total'].sum()
                perc = (ocup / cap * 100) if cap > 0 else 0
                
                prestador_row.append(f"{cap}/{ocup}/{perc:.1f}%")
                total_cap += cap
                total_ocup += ocup
            
            total_perc = (total_ocup / total_cap * 100) if total_cap > 0 else 0
            prestador_row.append(f"{total_cap}/{total_ocup}/{total_perc:.1f}%")
            tabla_data.append(prestador_row)
            
            # Filas por sede
            for sede in df_prestador['nombre_sede_prestador'].unique():
                df_sede = df_prestador[df_prestador['nombre_sede_prestador'] == sede]
                
                sede_row = [f"  └─ {sede}"]
                
                sede_cap = 0
                sede_ocup = 0
                
                for tipo_servicio in ['observacion', 'cuidado_critico', 'hospitalizacion']:
                    df_servicio = df_sede[df_sede['tipo_servicio'] == tipo_servicio]
                    cap = df_servicio['cantidad_ci_TOTAL_REPS'].sum()
                    ocup = df_servicio['ocupacion_total'].sum()
                    perc = (ocup / cap * 100) if cap > 0 else 0
                    
                    if cap > 0:
                        sede_row.append(f"{cap}/{ocup}/{perc:.1f}%")
                    else:
                        sede_row.append("-")
                    
                    sede_cap += cap
                    sede_ocup += ocup
                
                sede_perc = (sede_ocup / sede_cap * 100) if sede_cap > 0 else 0
                if sede_cap > 0:
                    sede_row.append(f"{sede_cap}/{sede_ocup}/{sede_perc:.1f}%")
                else:
                    sede_row.append("-")
                
                tabla_data.append(sede_row)
        
        return [headers] + tabla_data
    
    def _crear_tabla_detallada_municipios(self):
        """Crear tabla detallada de todos los municipios."""
        stats_municipios = self._obtener_estadisticas_otros_municipios()
        
        if not stats_municipios:
            return None
        
        # Encabezados
        headers = [
            'Municipio',
            'Prestadores',
            'Sedes',
            'Observación\nCap./Ocup./(%)',
            'Cuidado Crítico\nCap./Ocup./(%)',
            'Hospitalización\nCap./Ocup./(%)',
            'Total General\nCap./Ocup./(%)',
            'Estado'
        ]
        
        tabla_data = [headers]
        
        for municipio_stats in stats_municipios:
            # Determinar estado según porcentaje
            porcentaje = municipio_stats['total_porcentaje']
            if porcentaje >= UMBRALES['critico']:
                estado = "🔴 CRÍTICO"
            elif porcentaje >= UMBRALES['advertencia']:
                estado = "🟡 ADVERTENCIA"
            else:
                estado = "🟢 NORMAL"
            
            fila = [
                municipio_stats['municipio'],
                str(municipio_stats['prestadores']),
                str(municipio_stats['sedes']),
                f"{municipio_stats['observacion_capacidad']}/{municipio_stats['observacion_ocupacion']}/{municipio_stats['observacion_porcentaje']:.1f}%",
                f"{municipio_stats['cuidado_critico_capacidad']}/{municipio_stats['cuidado_critico_ocupacion']}/{municipio_stats['cuidado_critico_porcentaje']:.1f}%",
                f"{municipio_stats['hospitalizacion_capacidad']}/{municipio_stats['hospitalizacion_ocupacion']}/{municipio_stats['hospitalizacion_porcentaje']:.1f}%",
                f"{municipio_stats['total_capacidad']}/{municipio_stats['total_ocupacion']}/{municipio_stats['total_porcentaje']:.1f}%",
                estado
            ]
            
            tabla_data.append(fila)
        
        return tabla_data
    
    def generar_informe_pdf(self, archivo_salida=None):
        """Generar el informe PDF con la nueva estructura."""
        if archivo_salida is None:
            timestamp = self.fecha_procesamiento.strftime("%Y%m%d_%H%M%S")
            archivo_salida = f"informe_tolima_servicios_{timestamp}.pdf"
        
        print(f"📄 Generando informe PDF: {archivo_salida}")
        
        # Configurar documento
        doc = SimpleDocTemplate(archivo_salida, pagesize=A4,
                              rightMargin=0.5*inch, leftMargin=0.5*inch,
                              topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Elementos del documento
        elementos = []
        
        # Estilos
        estilos = getSampleStyleSheet()
        
        titulo_principal = ParagraphStyle(
            'TituloPrincipal',
            parent=estilos['Title'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor(COLORS['primary']),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        titulo_seccion = ParagraphStyle(
            'TituloSeccion',
            parent=estilos['Heading1'],
            fontSize=14,
            spaceAfter=15,
            textColor=colors.HexColor(COLORS['primary']),
            fontName='Helvetica-Bold'
        )
        
        titulo_subseccion = ParagraphStyle(
            'TituloSubseccion',
            parent=estilos['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.HexColor(COLORS['accent']),
            fontName='Helvetica-Bold'
        )
        
        texto_normal = ParagraphStyle(
            'TextoNormal',
            parent=estilos['Normal'],
            fontSize=10,
            spaceAfter=10,
            alignment=TA_JUSTIFY
        )
        
        # ======================================================================
        # PORTADA
        # ======================================================================
        elementos.append(Spacer(1, 1*inch))
        
        elementos.append(Paragraph("INFORME DE CAPACIDAD HOSPITALARIA", titulo_principal))
        elementos.append(Paragraph("DEPARTAMENTO DEL TOLIMA", titulo_principal))
        elementos.append(Paragraph("Análisis por Tipos de Servicio", titulo_seccion))
        
        elementos.append(Spacer(1, 0.5*inch))
        
        fecha_str = self.fecha_procesamiento.strftime("%d de %B de %Y")
        elementos.append(Paragraph(f"<b>Fecha de Procesamiento:</b> {fecha_str}", texto_normal))
        elementos.append(Paragraph(f"<b>Secretaría de Salud del Tolima</b>", texto_normal))
        elementos.append(Paragraph(f"<b>Sistema de Monitoreo Hospitalario</b>", texto_normal))
        
        elementos.append(PageBreak())
        
        # ======================================================================
        # 1. RESUMEN EJECUTIVO DEL TOLIMA
        # ======================================================================
        elementos.append(Paragraph("1. RESUMEN EJECUTIVO - DEPARTAMENTO DEL TOLIMA", titulo_seccion))
        
        stats_tolima = self._obtener_estadisticas_tolima()
        
        elementos.append(Paragraph("📊 <b>Estadísticas Generales del Departamento</b>", titulo_subseccion))
        
        resumen_texto = f"""
        <b>Cobertura Territorial:</b><br/>
        • Total de municipios con reporte: {stats_tolima['general']['total_municipios']}<br/>
        • Prestadores de salud activos: {stats_tolima['general']['total_prestadores']}<br/>
        • Sedes hospitalarias registradas: {stats_tolima['general']['total_sedes']}<br/><br/>
        
        <b>Capacidad Hospitalaria Departamental:</b><br/>
        • Capacidad total instalada: {stats_tolima['general']['capacidad_total_departamento']} unidades<br/>
        • Ocupación actual: {stats_tolima['general']['ocupacion_total_departamento']} pacientes<br/>
        • Porcentaje de ocupación: {stats_tolima['general']['porcentaje_ocupacion_departamento']:.1f}%<br/><br/>
        """
        
        elementos.append(Paragraph(resumen_texto, texto_normal))
        
        # Estadísticas por tipo de servicio
        elementos.append(Paragraph("🏥 <b>Análisis por Tipos de Servicio</b>", titulo_subseccion))
        
        for tipo_servicio, info in self.mapeo_servicios.items():
            if tipo_servicio in stats_tolima:
                stats = stats_tolima[tipo_servicio]
                
                # Determinar estado
                porcentaje = stats['porcentaje_ocupacion']
                if porcentaje >= UMBRALES['critico']:
                    estado = "🔴 CRÍTICO"
                    estado_desc = "requiere atención inmediata"
                elif porcentaje >= UMBRALES['advertencia']:
                    estado = "🟡 ADVERTENCIA"
                    estado_desc = "requiere monitoreo"
                else:
                    estado = "🟢 NORMAL"
                    estado_desc = "funcionando dentro de parámetros normales"
                
                servicio_texto = f"""
                <b>{info['nombre']} - {estado}</b><br/>
                • Capacidad instalada: {stats['capacidad_total']} unidades<br/>
                • Ocupación actual: {stats['ocupacion_total']} pacientes ({stats['porcentaje_ocupacion']:.1f}%)<br/>
                • Pacientes COVID-19: {stats['ocupacion_covid']}<br/>
                • Pacientes No COVID-19: {stats['ocupacion_no_covid']}<br/>
                • Unidades disponibles: {stats['disponible']}<br/>
                • Estado: <i>{estado_desc}</i><br/><br/>
                """
                
                elementos.append(Paragraph(servicio_texto, texto_normal))
        
        # Gráfico del Tolima
        grafico_tolima = self._crear_grafico_tolima_servicios()
        if grafico_tolima and os.path.exists(grafico_tolima):
            elementos.append(Spacer(1, 0.2*inch))
            elementos.append(Image(grafico_tolima, width=7*inch, height=4*inch))
            elementos.append(Spacer(1, 0.2*inch))
        
        elementos.append(PageBreak())
        
        # ======================================================================
        # 2. ANÁLISIS DETALLADO DE IBAGUÉ
        # ======================================================================
        elementos.append(Paragraph("2. ANÁLISIS DETALLADO - IBAGUÉ (CAPITAL)", titulo_seccion))
        
        stats_ibague = self._obtener_estadisticas_ibague()
        
        if stats_ibague:
            elementos.append(Paragraph("🏛️ <b>Ibagué como Centro de Referencia Departamental</b>", titulo_subseccion))
            
            # Calcular totales de Ibagué
            total_cap_ibague = sum(stats_ibague[tipo]['capacidad_total'] for tipo in self.mapeo_servicios.keys())
            total_ocup_ibague = sum(stats_ibague[tipo]['ocupacion_total'] for tipo in self.mapeo_servicios.keys())
            porcentaje_ibague = (total_ocup_ibague / total_cap_ibague * 100) if total_cap_ibague > 0 else 0
            
            participacion_capacidad = (total_cap_ibague / stats_tolima['general']['capacidad_total_departamento'] * 100)
            participacion_ocupacion = (total_ocup_ibague / stats_tolima['general']['ocupacion_total_departamento'] * 100)
            
            resumen_ibague = f"""
            <b>Participación de Ibagué en el Sistema Departamental:</b><br/>
            • Participación en capacidad total: {participacion_capacidad:.1f}% del departamento<br/>
            • Participación en ocupación: {participacion_ocupacion:.1f}% del departamento<br/>
            • Capacidad total de Ibagué: {total_cap_ibague} unidades<br/>
            • Ocupación actual: {total_ocup_ibague} pacientes ({porcentaje_ibague:.1f}%)<br/><br/>
            """
            
            elementos.append(Paragraph(resumen_ibague, texto_normal))
            
            # Análisis por servicio en Ibagué
            elementos.append(Paragraph("📋 <b>Detalle por Tipo de Servicio en Ibagué</b>", titulo_subseccion))
            
            for tipo_servicio, info in self.mapeo_servicios.items():
                if tipo_servicio in stats_ibague:
                    stats = stats_ibague[tipo_servicio]
                    
                    participacion_servicio = (stats['capacidad_total'] / total_cap_ibague * 100) if total_cap_ibague > 0 else 0
                    
                    servicio_ibague = f"""
                    <b>{info['nombre']}:</b><br/>
                    • Prestadores: {stats['prestadores']} | Sedes: {stats['sedes']}<br/>
                    • Capacidad: {stats['capacidad_total']} unidades ({participacion_servicio:.1f}% del total de Ibagué)<br/>
                    • Ocupación: {stats['ocupacion_total']} pacientes ({stats['porcentaje_ocupacion']:.1f}%)<br/>
                    • COVID-19: {stats['ocupacion_covid']} | No COVID-19: {stats['ocupacion_no_covid']}<br/>
                    • Disponibles: {stats['disponible']} unidades<br/><br/>
                    """
                    
                    elementos.append(Paragraph(servicio_ibague, texto_normal))
            
            # Gráfico detallado de Ibagué
            grafico_ibague = self._crear_grafico_ibague_detallado()
            if grafico_ibague and os.path.exists(grafico_ibague):
                elementos.append(Spacer(1, 0.2*inch))
                elementos.append(Image(grafico_ibague, width=7*inch, height=5.5*inch))
                elementos.append(Spacer(1, 0.2*inch))
            
            # Tabla detallada de Ibagué
            tabla_ibague = self._crear_tabla_detallada_ibague()
            if tabla_ibague:
                elementos.append(Paragraph("📊 <b>Tabla Detallada por Prestador y Sede - Ibagué</b>", titulo_subseccion))
                
                # Crear tabla para PDF
                tabla_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primary'])),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ])
                
                tabla_pdf = Table(tabla_ibague, repeatRows=1)
                tabla_pdf.setStyle(tabla_style)
                elementos.append(tabla_pdf)
        
        elementos.append(PageBreak())
        
        # ======================================================================
        # 3. ANÁLISIS DE OTROS MUNICIPIOS
        # ======================================================================
        elementos.append(Paragraph("3. ANÁLISIS DE OTROS MUNICIPIOS DEL TOLIMA", titulo_seccion))
        
        stats_otros = self._obtener_estadisticas_otros_municipios()
        
        if stats_otros:
            # Resumen de otros municipios
            total_otros_cap = sum(m['total_capacidad'] for m in stats_otros)
            total_otros_ocup = sum(m['total_ocupacion'] for m in stats_otros)
            porcentaje_otros = (total_otros_ocup / total_otros_cap * 100) if total_otros_cap > 0 else 0
            
            municipios_criticos = [m for m in stats_otros if m['total_porcentaje'] >= UMBRALES['critico']]
            municipios_advertencia = [m for m in stats_otros if UMBRALES['advertencia'] <= m['total_porcentaje'] < UMBRALES['critico']]
            
            resumen_otros = f"""
            <b>Panorama de Municipios (Excluyendo Ibagué):</b><br/>
            • Total de municipios analizados: {len(stats_otros)}<br/>
            • Capacidad total combinada: {total_otros_cap} unidades<br/>
            • Ocupación total: {total_otros_ocup} pacientes ({porcentaje_otros:.1f}%)<br/>
            • Municipios en estado crítico (≥90%): {len(municipios_criticos)}<br/>
            • Municipios en advertencia (70-89%): {len(municipios_advertencia)}<br/><br/>
            """
            
            elementos.append(Paragraph(resumen_otros, texto_normal))
            
            # Alertas críticas
            if municipios_criticos:
                elementos.append(Paragraph("🚨 <b>MUNICIPIOS EN ESTADO CRÍTICO</b>", titulo_subseccion))
                
                for municipio in municipios_criticos:
                    alerta_texto = f"""
                    <b>{municipio['municipio']}</b> - {municipio['total_porcentaje']:.1f}% de ocupación<br/>
                    • Capacidad: {municipio['total_capacidad']} | Ocupación: {municipio['total_ocupacion']}<br/>
                    • Prestadores: {municipio['prestadores']} | Sedes: {municipio['sedes']}<br/><br/>
                    """
                    elementos.append(Paragraph(alerta_texto, texto_normal))
            
            # Gráfico de otros municipios
            grafico_otros = self._crear_grafico_otros_municipios()
            if grafico_otros and os.path.exists(grafico_otros):
                elementos.append(Spacer(1, 0.2*inch))
                elementos.append(Image(grafico_otros, width=7*inch, height=5.5*inch))
                elementos.append(Spacer(1, 0.2*inch))
            
            # Tabla detallada de municipios
            tabla_municipios = self._crear_tabla_detallada_municipios()
            if tabla_municipios:
                elementos.append(Paragraph("📊 <b>Tabla Detallada de Todos los Municipios</b>", titulo_subseccion))
                
                tabla_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primary'])),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 7),
                    ('FONTSIZE', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ])
                
                # Colorear filas según estado
                for i, fila in enumerate(tabla_municipios[1:], 1):
                    if "CRÍTICO" in fila[-1]:
                        tabla_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FFEBEE'))
                    elif "ADVERTENCIA" in fila[-1]:
                        tabla_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FFF3E0'))
                
                tabla_pdf = Table(tabla_municipios, repeatRows=1)
                tabla_pdf.setStyle(tabla_style)
                elementos.append(tabla_pdf)
        
        # ======================================================================
        # 4. CONCLUSIONES Y RECOMENDACIONES
        # ======================================================================
        elementos.append(PageBreak())
        elementos.append(Paragraph("4. CONCLUSIONES Y RECOMENDACIONES", titulo_seccion))
        
        # Generar conclusiones automáticas
        conclusiones = self._generar_conclusiones(stats_tolima, stats_ibague, stats_otros)
        elementos.append(Paragraph(conclusiones, texto_normal))
        
        # Pie de página
        elementos.append(Spacer(1, 1*inch))
        pie_texto = f"""
        <b>Informe generado por:</b> Sistema de Monitoreo Hospitalario<br/>
        <b>Secretaría de Salud del Tolima</b><br/>
        <b>Fecha y hora:</b> {self.fecha_procesamiento.strftime("%d/%m/%Y %H:%M:%S")}<br/>
        <b>Desarrollado por:</b> Ing. José Miguel Santos
        """
        elementos.append(Paragraph(pie_texto, texto_normal))
        
        # Construir documento
        try:
            doc.build(elementos)
            print(f"✅ Informe PDF generado exitosamente: {archivo_salida}")
            return archivo_salida
        except Exception as e:
            print(f"❌ Error generando PDF: {str(e)}")
            return None
    
    def _generar_conclusiones(self, stats_tolima, stats_ibague, stats_otros):
        """Generar conclusiones automáticas basadas en los datos."""
        conclusiones = []
        
        # Análisis departamental
        porcentaje_dept = stats_tolima['general']['porcentaje_ocupacion_departamento']
        if porcentaje_dept >= UMBRALES['critico']:
            conclusiones.append("🔴 <b>SITUACIÓN CRÍTICA DEPARTAMENTAL:</b> El Tolima presenta una ocupación hospitalaria crítica que requiere activación de protocolos de emergencia y redistribución de pacientes.")
        elif porcentaje_dept >= UMBRALES['advertencia']:
            conclusiones.append("🟡 <b>SITUACIÓN DE ADVERTENCIA:</b> El departamento del Tolima requiere monitoreo constante y preparación de medidas preventivas.")
        else:
            conclusiones.append("🟢 <b>SITUACIÓN CONTROLADA:</b> El sistema hospitalario del Tolima opera dentro de parámetros normales.")
        
        # Análisis por servicios
        for tipo_servicio, info in self.mapeo_servicios.items():
            if tipo_servicio in stats_tolima:
                porcentaje = stats_tolima[tipo_servicio]['porcentaje_ocupacion']
                if porcentaje >= UMBRALES['critico']:
                    conclusiones.append(f"⚠️ El servicio de <b>{info['nombre']}</b> presenta ocupación crítica ({porcentaje:.1f}%) y requiere atención inmediata.")
        
        # Análisis de Ibagué
        if stats_ibague:
            total_cap_ibague = sum(stats_ibague[tipo]['capacidad_total'] for tipo in self.mapeo_servicios.keys())
            participacion = (total_cap_ibague / stats_tolima['general']['capacidad_total_departamento'] * 100)
            conclusiones.append(f"🏛️ <b>PAPEL DE IBAGUÉ:</b> Como capital concentra el {participacion:.1f}% de la capacidad hospitalaria departamental, siendo el principal centro de referencia.")
        
        # Análisis de municipios
        if stats_otros:
            municipios_criticos = [m for m in stats_otros if m['total_porcentaje'] >= UMBRALES['critico']]
            if municipios_criticos:
                nombres = ", ".join([m['municipio'] for m in municipios_criticos[:3]])
                if len(municipios_criticos) > 3:
                    nombres += f" y {len(municipios_criticos)-3} más"
                conclusiones.append(f"🚨 <b>MUNICIPIOS CRÍTICOS:</b> {nombres} requieren apoyo inmediato de la red departamental.")
        
        # Recomendaciones
        recomendaciones = [
            "📋 <b>RECOMENDACIONES INMEDIATAS:</b>",
            "• Activar protocolos de referencia y contrarreferencia entre municipios",
            "• Fortalecer la coordinación entre Ibagué y municipios periféricos",
            "• Implementar monitoreo en tiempo real de ocupación por servicios",
            "• Preparar planes de contingencia para redistribución de pacientes",
            "• Reforzar personal médico en servicios con mayor ocupación"
        ]
        
        return "<br/>".join(conclusiones + ["<br/>"] + recomendaciones)


def main():
    """Función principal del programa."""
    print("🏥" + "="*70)
    print("   GENERADOR DE INFORMES DE CAPACIDAD HOSPITALARIA")
    print("           DEPARTAMENTO DEL TOLIMA - POR SERVICIOS")
    print("="*72)
    print("   Desarrollado por: Ing. José Miguel Santos")
    print("   Para: Secretaría de Salud del Tolima")
    print("="*72)
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("📋 USO DEL PROGRAMA:")
        print("   python hospital_report.py <archivo_excel> [archivo_salida.pdf]")
        print("")
        print("📊 EJEMPLOS:")
        print("   python hospital_report.py datos_hospitalarios.xlsx")
        print("   python hospital_report.py datos_hospitalarios.xlsx informe_tolima.pdf")
        print("")
        print("🔧 CARACTERÍSTICAS:")
        print("   ✅ Análisis por tipos de servicio (Observación, Crítico, Hospitalización)")
        print("   ✅ Estructura: Tolima → Ibagué → Otros Municipios")
        print("   ✅ Gráficos optimizados y proporcionales")
        print("   ✅ Tablas detalladas por prestador y sede")
        print("   ✅ Alertas automáticas por umbrales de ocupación")
        print("   ✅ Análisis COVID-19 vs No COVID-19")
        return
    
    archivo_excel = sys.argv[1]
    archivo_salida = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Verificar que el archivo existe
    if not os.path.exists(archivo_excel):
        print(f"❌ Error: El archivo '{archivo_excel}' no existe.")
        return
    
    # Crear generador de informes
    generador = HospitalReportGenerator()
    
    try:
        # Cargar datos
        if not generador.cargar_datos(archivo_excel):
            print("❌ Error al cargar los datos. Verifique el formato del archivo.")
            return
        
        # Generar informe
        archivo_generado = generador.generar_informe_pdf(archivo_salida)
        
        if archivo_generado:
            print("🎉" + "="*70)
            print("✅ INFORME GENERADO EXITOSAMENTE")
            print(f"📄 Archivo: {archivo_generado}")
            print(f"📊 Datos procesados: {len(generador.df)} registros")
            print(f"🏥 Municipios: {generador.df['municipio_sede_prestador'].nunique()}")
            print(f"🏛️ Prestadores: {generador.df['nombre_prestador'].nunique()}")
            print(f"📍 Sedes: {generador.df['nombre_sede_prestador'].nunique()}")
            print("="*72)
            print("🔍 ESTRUCTURA DEL INFORME:")
            print("   1. Resumen Ejecutivo del Tolima")
            print("   2. Análisis Detallado de Ibagué")
            print("   3. Análisis de Otros Municipios")
            print("   4. Conclusiones y Recomendaciones")
            print("="*72)
        else:
            print("❌ Error al generar el informe PDF.")
            
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpiar archivos temporales de gráficos
        archivos_temp = [
            'grafico_tolima_servicios.png',
            'grafico_ibague_detallado.png', 
            'grafico_otros_municipios.png'
        ]
        
        for archivo in archivos_temp:
            if os.path.exists(archivo):
                try:
                    os.remove(archivo)
                except:
                    pass


if __name__ == "__main__":
    main()