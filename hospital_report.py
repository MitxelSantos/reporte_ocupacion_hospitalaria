#!/usr/bin/env python3
"""
Generador de Informes de Capacidad Hospitalaria - Departamento del Tolima
Estructura por Servicios y Niveles de Atención

COLUMNAS PRINCIPALES:
- municipio_sede_prestador: Municipio del departamento
- nombre_prestador: Prestador de salud (puede tener varias sedes)
- nivel_de_atencion_prestador: Nivel de complejidad (I, II, III, IV)
- nombre_sede_prestador: Nombre de la sede específica
- nombre_capacidad_instalada: Tipo de cama/camilla y sección
- cantidad_ci_TOTAL_REPS: Capacidad total
- total_ingresos_paciente_servicio: Pacientes ingresados (ocupación)

Estructura: Tolima → Ibagué → Federico Lleras → Otros Municipios

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
    """Generador de informes de capacidad hospitalaria optimizado por servicios y niveles."""
    
    def __init__(self):
        """Inicializar el generador de reportes."""
        self.df = None
        self.fecha_procesamiento = datetime.now()
        self.mapeo_servicios = self._crear_mapeo_servicios()
        self.mapeo_niveles = self._crear_mapeo_niveles()
        
    def _crear_mapeo_servicios(self):
        """Crear mapeo de capacidades a tipos de servicio."""
        return {
            'observacion': {
                'nombre': 'Observación/Urgencias',
                'descripcion': 'Servicios de urgencias y observación',
                'keywords': [
                    'observacion', 'observación', 'urgencias', 'urgencia', 'emergencia', 'emergencias',
                    'camilla', 'camillas', 'consulta externa', 'triage', 'clasificacion',
                    'camilla de observacion', 'camilla observacion', 'emergencia adulto',
                    'emergencia pediatric', 'consulta', 'procedimientos', 'sala de procedimientos'
                ],
                'color': COLORS['warning']
            },
            'cuidado_critico': {
                'nombre': 'Cuidado Crítico',
                'descripcion': 'UCI y Cuidado Intermedio',
                'keywords': [
                    'uci', 'UCI', 'cuidado intensivo', 'cuidado intermedio', 'intensivo', 'intermedio',
                    'unidad de cuidado intensivo', 'unidad cuidado intermedio', 'cuidados intensivos',
                    'cuidados intermedios', 'critico', 'crítico', 'coronario', 'reanimacion'
                ],
                'color': COLORS['danger']
            },
            'hospitalizacion': {
                'nombre': 'Hospitalización',
                'descripcion': 'Servicios de hospitalización general',
                'keywords': [
                    'adulto', 'adultos', 'pediatric', 'pediátric', 'pediatria', 'gineco', 'ginecologia',
                    'medicina', 'cirugia', 'cirugía', 'general', 'hospitalizacion', 'hospitalización',
                    'cama', 'camas', 'internacion', 'internación', 'sala', 'piso', 'habitacion',
                    'maternidad', 'obstetricia', 'neonatal', 'recien nacido', 'lactantes'
                ],
                'color': COLORS['primary']
            }
        }
    
    def _crear_mapeo_niveles(self):
        """Crear mapeo de niveles de atención."""
        return {
            'I': {'nombre': 'Nivel I', 'descripcion': 'Baja complejidad', 'color': COLORS['success']},
            'II': {'nombre': 'Nivel II', 'descripcion': 'Mediana complejidad', 'color': COLORS['secondary']},
            'III': {'nombre': 'Nivel III', 'descripcion': 'Alta complejidad', 'color': COLORS['primary']},
            'IV': {'nombre': 'Nivel IV', 'descripcion': 'Muy alta complejidad', 'color': COLORS['danger']}
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
    
    def _limpiar_nivel_atencion(self, nivel):
        """Limpiar y estandarizar el nivel de atención."""
        if pd.isna(nivel):
            return 'N/A'
        
        nivel_str = str(nivel).strip().upper()
        
        # Extraer número romano o arábigo
        if 'I' in nivel_str and 'V' not in nivel_str:
            if nivel_str.count('I') == 1:
                return 'I'
            elif nivel_str.count('I') == 2:
                return 'II'
            elif nivel_str.count('I') == 3:
                return 'III'
        elif 'IV' in nivel_str or '4' in nivel_str:
            return 'IV'
        elif 'III' in nivel_str or '3' in nivel_str:
            return 'III'
        elif 'II' in nivel_str or '2' in nivel_str:
            return 'II'
        elif '1' in nivel_str:
            return 'I'
        
        return 'N/A'
    
    def cargar_datos(self, archivo_excel):
        """Cargar y procesar datos del archivo Excel."""
        try:
            print(f"📂 Cargando datos desde: {archivo_excel}")
            
            # Cargar datos
            self.df = pd.read_excel(archivo_excel)
            print(f"📊 Datos cargados: {len(self.df)} registros")
            
            # Verificar columnas esenciales
            columnas_requeridas = [
                'municipio_sede_prestador',
                'nombre_prestador', 
                'nivel_de_atencion_prestador',
                'nombre_sede_prestador',
                'nombre_capacidad_instalada',
                'cantidad_ci_TOTAL_REPS',
                'total_ingresos_paciente_servicio'
            ]
            
            columnas_faltantes = [col for col in columnas_requeridas if col not in self.df.columns]
            if columnas_faltantes:
                print(f"❌ Error: Columnas faltantes: {columnas_faltantes}")
                print(f"📋 Columnas disponibles: {list(self.df.columns)}")
                return False
            
            # Procesar datos
            self._procesar_datos()
            print("✅ Datos procesados exitosamente")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar datos: {str(e)}")
            return False
    
    def _procesar_datos(self):
        """Procesar y limpiar los datos cargados."""
        print("🔄 Procesando datos...")
        
        # Limpiar nombres de columnas
        self.df.columns = self.df.columns.str.strip()
        
        # Convertir valores numéricos
        self.df['cantidad_ci_TOTAL_REPS'] = pd.to_numeric(self.df['cantidad_ci_TOTAL_REPS'], errors='coerce').fillna(0)
        self.df['total_ingresos_paciente_servicio'] = pd.to_numeric(self.df['total_ingresos_paciente_servicio'], errors='coerce').fillna(0)
        
        # Calcular porcentaje de ocupación
        self.df['porcentaje_ocupacion'] = np.where(
            self.df['cantidad_ci_TOTAL_REPS'] > 0,
            (self.df['total_ingresos_paciente_servicio'] / self.df['cantidad_ci_TOTAL_REPS']) * 100,
            0
        )
        
        # Calcular disponibilidad
        self.df['disponible'] = self.df['cantidad_ci_TOTAL_REPS'] - self.df['total_ingresos_paciente_servicio']
        self.df['disponible'] = self.df['disponible'].clip(lower=0)  # No puede ser negativo
        
        # Limpiar y estandarizar nombres
        self.df['municipio_sede_prestador'] = self.df['municipio_sede_prestador'].str.strip().str.title()
        self.df['nombre_prestador'] = self.df['nombre_prestador'].str.strip()
        self.df['nombre_sede_prestador'] = self.df['nombre_sede_prestador'].str.strip()
        self.df['nombre_capacidad_instalada'] = self.df['nombre_capacidad_instalada'].str.strip()
        
        # Limpiar nivel de atención
        self.df['nivel_atencion_limpio'] = self.df['nivel_de_atencion_prestador'].apply(self._limpiar_nivel_atencion)
        
        # Asegurar que Ibagué esté bien escrito
        self.df['municipio_sede_prestador'] = self.df['municipio_sede_prestador'].replace(
            ['Ibague', 'IBAGUE', 'ibague'], 'Ibagué'
        )
        
        # DEBUG: Mostrar tipos de capacidad instalada únicos
        print("🔍 TIPOS DE CAPACIDAD INSTALADA ENCONTRADOS:")
        tipos_unicos = self.df['nombre_capacidad_instalada'].unique()
        for i, tipo in enumerate(sorted(tipos_unicos), 1):
            print(f"   {i:2d}. {tipo}")
        print()
        
        # Clasificar por tipo de servicio
        self.df['tipo_servicio'] = self.df['nombre_capacidad_instalada'].apply(self._clasificar_servicio)
        
        # DEBUG: Mostrar clasificación por servicio
        print("📊 CLASIFICACIÓN POR TIPO DE SERVICIO:")
        clasificacion = self.df.groupby('tipo_servicio').agg({
            'cantidad_ci_TOTAL_REPS': 'sum',
            'total_ingresos_paciente_servicio': 'sum',
            'nombre_capacidad_instalada': 'nunique'
        }).reset_index()
        
        for _, row in clasificacion.iterrows():
            porcentaje = (row['total_ingresos_paciente_servicio'] / row['cantidad_ci_TOTAL_REPS'] * 100) if row['cantidad_ci_TOTAL_REPS'] > 0 else 0
            print(f"   🔹 {row['tipo_servicio'].upper()}:")
            print(f"      • Capacidad: {row['cantidad_ci_TOTAL_REPS']:,} unidades")
            print(f"      • Ocupación: {row['total_ingresos_paciente_servicio']:,} pacientes ({porcentaje:.1f}%)")
            print(f"      • Tipos diferentes: {row['nombre_capacidad_instalada']}")
        print()
        
        # Crear identificadores únicos
        self.df['prestador_sede'] = self.df['nombre_prestador'] + " - " + self.df['nombre_sede_prestador']
        
        print(f"📊 Procesamiento completado:")
        print(f"   🏘️  Municipios: {self.df['municipio_sede_prestador'].nunique()}")
        print(f"   🏥 Prestadores: {self.df['nombre_prestador'].nunique()}")
        print(f"   🏢 Sedes: {self.df['nombre_sede_prestador'].nunique()}")
        print(f"   📋 Tipos de capacidad: {self.df['nombre_capacidad_instalada'].nunique()}")
        print(f"   🎯 Servicios: {self.df['tipo_servicio'].value_counts().to_dict()}")
        print(f"   🔢 Niveles: {self.df['nivel_atencion_limpio'].value_counts().to_dict()}")
        print()
        
        # Verificar si hay datos para observación/urgencias
        obs_data = self.df[self.df['tipo_servicio'] == 'observacion']
        if obs_data.empty:
            print("⚠️  WARNING: No se encontraron datos para OBSERVACIÓN/URGENCIAS")
            print("    Verificando keywords utilizadas...")
            
            # Mostrar algunos ejemplos que podrían ser observación
            ejemplos_posibles = []
            for tipo in tipos_unicos:
                tipo_lower = tipo.lower()
                if any(word in tipo_lower for word in ['observ', 'urgenc', 'emergen', 'camilla', 'consult']):
                    ejemplos_posibles.append(tipo)
            
            if ejemplos_posibles:
                print("    Posibles tipos que deberían ser observación:")
                for ejemplo in ejemplos_posibles[:5]:
                    print(f"      • {ejemplo}")
            print()
    
    def _obtener_estadisticas_tolima(self):
        """Obtener estadísticas generales del departamento del Tolima."""
        stats = {}
        
        # Totales por tipo de servicio
        for tipo_servicio in self.mapeo_servicios.keys():
            df_servicio = self.df[self.df['tipo_servicio'] == tipo_servicio]
            
            stats[tipo_servicio] = {
                'capacidad_total': int(df_servicio['cantidad_ci_TOTAL_REPS'].sum()),
                'ocupacion_total': int(df_servicio['total_ingresos_paciente_servicio'].sum()),
                'disponible': int(df_servicio['disponible'].sum()),
                'municipios': df_servicio['municipio_sede_prestador'].nunique(),
                'prestadores': df_servicio['nombre_prestador'].nunique(),
                'sedes': df_servicio['nombre_sede_prestador'].nunique()
            }
            
            # Calcular porcentaje
            if stats[tipo_servicio]['capacidad_total'] > 0:
                stats[tipo_servicio]['porcentaje_ocupacion'] = round(
                    (stats[tipo_servicio]['ocupacion_total'] / stats[tipo_servicio]['capacidad_total']) * 100, 1
                )
            else:
                stats[tipo_servicio]['porcentaje_ocupacion'] = 0
        
        # Totales por nivel de atención
        stats['niveles'] = {}
        for nivel in ['I', 'II', 'III', 'IV', 'N/A']:
            df_nivel = self.df[self.df['nivel_atencion_limpio'] == nivel]
            
            if len(df_nivel) > 0:
                stats['niveles'][nivel] = {
                    'capacidad_total': int(df_nivel['cantidad_ci_TOTAL_REPS'].sum()),
                    'ocupacion_total': int(df_nivel['total_ingresos_paciente_servicio'].sum()),
                    'disponible': int(df_nivel['disponible'].sum()),
                    'municipios': df_nivel['municipio_sede_prestador'].nunique(),
                    'prestadores': df_nivel['nombre_prestador'].nunique()
                }
                
                if stats['niveles'][nivel]['capacidad_total'] > 0:
                    stats['niveles'][nivel]['porcentaje_ocupacion'] = round(
                        (stats['niveles'][nivel]['ocupacion_total'] / stats['niveles'][nivel]['capacidad_total']) * 100, 1
                    )
                else:
                    stats['niveles'][nivel]['porcentaje_ocupacion'] = 0
        
        # Estadísticas generales
        stats['general'] = {
            'total_municipios': self.df['municipio_sede_prestador'].nunique(),
            'total_prestadores': self.df['nombre_prestador'].nunique(),
            'total_sedes': self.df['nombre_sede_prestador'].nunique(),
            'capacidad_total_departamento': int(self.df['cantidad_ci_TOTAL_REPS'].sum()),
            'ocupacion_total_departamento': int(self.df['total_ingresos_paciente_servicio'].sum()),
            'disponible_total_departamento': int(self.df['disponible'].sum())
        }
        
        if stats['general']['capacidad_total_departamento'] > 0:
            stats['general']['porcentaje_ocupacion_departamento'] = round(
                (stats['general']['ocupacion_total_departamento'] / stats['general']['capacidad_total_departamento']) * 100, 1
            )
        else:
            stats['general']['porcentaje_ocupacion_departamento'] = 0
        
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
                'capacidad_total': int(df_servicio['cantidad_ci_TOTAL_REPS'].sum()),
                'ocupacion_total': int(df_servicio['total_ingresos_paciente_servicio'].sum()),
                'disponible': int(df_servicio['disponible'].sum()),
                'prestadores': df_servicio['nombre_prestador'].nunique(),
                'sedes': df_servicio['nombre_sede_prestador'].nunique()
            }
            
            if stats[tipo_servicio]['capacidad_total'] > 0:
                stats[tipo_servicio]['porcentaje_ocupacion'] = round(
                    (stats[tipo_servicio]['ocupacion_total'] / stats[tipo_servicio]['capacidad_total']) * 100, 1
                )
            else:
                stats[tipo_servicio]['porcentaje_ocupacion'] = 0
        
        # Por nivel de atención
        stats['niveles'] = {}
        for nivel in ['I', 'II', 'III', 'IV', 'N/A']:
            df_nivel = df_ibague[df_ibague['nivel_atencion_limpio'] == nivel]
            
            if len(df_nivel) > 0:
                stats['niveles'][nivel] = {
                    'capacidad_total': int(df_nivel['cantidad_ci_TOTAL_REPS'].sum()),
                    'ocupacion_total': int(df_nivel['total_ingresos_paciente_servicio'].sum()),
                    'disponible': int(df_nivel['disponible'].sum()),
                    'prestadores': df_nivel['nombre_prestador'].nunique(),
                    'sedes': df_nivel['nombre_sede_prestador'].nunique()
                }
                
                if stats['niveles'][nivel]['capacidad_total'] > 0:
                    stats['niveles'][nivel]['porcentaje_ocupacion'] = round(
                        (stats['niveles'][nivel]['ocupacion_total'] / stats['niveles'][nivel]['capacidad_total']) * 100, 1
                    )
                else:
                    stats['niveles'][nivel]['porcentaje_ocupacion'] = 0
        
        # Totales de Ibagué
        stats['total'] = {
            'capacidad_total': int(df_ibague['cantidad_ci_TOTAL_REPS'].sum()),
            'ocupacion_total': int(df_ibague['total_ingresos_paciente_servicio'].sum()),
            'disponible': int(df_ibague['disponible'].sum()),
            'prestadores': df_ibague['nombre_prestador'].nunique(),
            'sedes': df_ibague['nombre_sede_prestador'].nunique()
        }
        
        if stats['total']['capacidad_total'] > 0:
            stats['total']['porcentaje_ocupacion'] = round(
                (stats['total']['ocupacion_total'] / stats['total']['capacidad_total']) * 100, 1
            )
        else:
            stats['total']['porcentaje_ocupacion'] = 0
        
        return stats
    
    def _obtener_estadisticas_federico_lleras(self):
        """Obtener estadísticas específicas del Hospital Federico Lleras Acosta."""
        # Buscar variaciones del nombre
        nombres_federico = [
            'FEDERICO LLERAS ACOSTA', 'Federico Lleras Acosta', 'federico lleras acosta',
            'HOSPITAL FEDERICO LLERAS', 'Hospital Federico Lleras', 'hospital federico lleras',
            'FEDERICO LLERAS', 'Federico Lleras', 'federico lleras',
            'LLERAS ACOSTA', 'Lleras Acosta', 'lleras acosta',
            'HFL', 'HFLLA'
        ]
        
        df_federico = None
        nombre_encontrado = None
        
        # Buscar el prestador con alguno de estos nombres
        for nombre in nombres_federico:
            df_temp = self.df[self.df['nombre_prestador'].str.contains(nombre, case=False, na=False)]
            if not df_temp.empty:
                df_federico = df_temp
                nombre_encontrado = nombre
                break
        
        if df_federico is None or df_federico.empty:
            return None
        
        stats = {'nombre_encontrado': nombre_encontrado}
        
        # Por tipo de servicio
        for tipo_servicio in self.mapeo_servicios.keys():
            df_servicio = df_federico[df_federico['tipo_servicio'] == tipo_servicio]
            
            stats[tipo_servicio] = {
                'capacidad_total': int(df_servicio['cantidad_ci_TOTAL_REPS'].sum()),
                'ocupacion_total': int(df_servicio['total_ingresos_paciente_servicio'].sum()),
                'disponible': int(df_servicio['disponible'].sum()),
                'sedes': df_servicio['nombre_sede_prestador'].nunique(),
                'tipos_capacidad': df_servicio['nombre_capacidad_instalada'].nunique()
            }
            
            if stats[tipo_servicio]['capacidad_total'] > 0:
                stats[tipo_servicio]['porcentaje_ocupacion'] = round(
                    (stats[tipo_servicio]['ocupacion_total'] / stats[tipo_servicio]['capacidad_total']) * 100, 1
                )
            else:
                stats[tipo_servicio]['porcentaje_ocupacion'] = 0
        
        # Por nivel de atención
        stats['niveles'] = {}
        for nivel in ['I', 'II', 'III', 'IV', 'N/A']:
            df_nivel = df_federico[df_federico['nivel_atencion_limpio'] == nivel]
            
            if len(df_nivel) > 0:
                stats['niveles'][nivel] = {
                    'capacidad_total': int(df_nivel['cantidad_ci_TOTAL_REPS'].sum()),
                    'ocupacion_total': int(df_nivel['total_ingresos_paciente_servicio'].sum()),
                    'disponible': int(df_nivel['disponible'].sum()),
                    'sedes': df_nivel['nombre_sede_prestador'].nunique(),
                    'tipos_capacidad': df_nivel['nombre_capacidad_instalada'].nunique()
                }
                
                if stats['niveles'][nivel]['capacidad_total'] > 0:
                    stats['niveles'][nivel]['porcentaje_ocupacion'] = round(
                        (stats['niveles'][nivel]['ocupacion_total'] / stats['niveles'][nivel]['capacidad_total']) * 100, 1
                    )
                else:
                    stats['niveles'][nivel]['porcentaje_ocupacion'] = 0
        
        # Totales del Federico Lleras
        stats['total'] = {
            'capacidad_total': int(df_federico['cantidad_ci_TOTAL_REPS'].sum()),
            'ocupacion_total': int(df_federico['total_ingresos_paciente_servicio'].sum()),
            'disponible': int(df_federico['disponible'].sum()),
            'sedes': df_federico['nombre_sede_prestador'].nunique(),
            'municipios': df_federico['municipio_sede_prestador'].nunique(),
            'tipos_capacidad': df_federico['nombre_capacidad_instalada'].nunique()
        }
        
        if stats['total']['capacidad_total'] > 0:
            stats['total']['porcentaje_ocupacion'] = round(
                (stats['total']['ocupacion_total'] / stats['total']['capacidad_total']) * 100, 1
            )
        else:
            stats['total']['porcentaje_ocupacion'] = 0
        
        # Detalles por sede
        stats['sedes'] = []
        for sede in df_federico['nombre_sede_prestador'].unique():
            df_sede = df_federico[df_federico['nombre_sede_prestador'] == sede]
            
            sede_stats = {
                'nombre': sede,
                'municipio': df_sede['municipio_sede_prestador'].iloc[0] if len(df_sede) > 0 else 'N/A',
                'nivel': df_sede['nivel_atencion_limpio'].mode().iloc[0] if len(df_sede['nivel_atencion_limpio'].mode()) > 0 else 'N/A',
                'capacidad_total': int(df_sede['cantidad_ci_TOTAL_REPS'].sum()),
                'ocupacion_total': int(df_sede['total_ingresos_paciente_servicio'].sum()),
                'disponible': int(df_sede['disponible'].sum()),
                'tipos_capacidad': df_sede['nombre_capacidad_instalada'].nunique()
            }
            
            if sede_stats['capacidad_total'] > 0:
                sede_stats['porcentaje_ocupacion'] = round(
                    (sede_stats['ocupacion_total'] / sede_stats['capacidad_total']) * 100, 1
                )
            else:
                sede_stats['porcentaje_ocupacion'] = 0
            
            # Por servicio en esta sede
            for tipo_servicio in self.mapeo_servicios.keys():
                df_servicio_sede = df_sede[df_sede['tipo_servicio'] == tipo_servicio]
                cap = int(df_servicio_sede['cantidad_ci_TOTAL_REPS'].sum())
                ocup = int(df_servicio_sede['total_ingresos_paciente_servicio'].sum())
                
                sede_stats[f'{tipo_servicio}_capacidad'] = cap
                sede_stats[f'{tipo_servicio}_ocupacion'] = ocup
                sede_stats[f'{tipo_servicio}_porcentaje'] = round((ocup / cap * 100), 1) if cap > 0 else 0
            
            stats['sedes'].append(sede_stats)
        
        return stats
    
    def _obtener_estadisticas_otros_municipios(self):
        """Obtener estadísticas de municipios diferentes a Ibagué."""
        df_otros = self.df[self.df['municipio_sede_prestador'] != 'Ibagué']
        
        if df_otros.empty:
            return None
        
        # Agrupar por municipio
        stats_municipios = []
        
        for municipio in df_otros['municipio_sede_prestador'].unique():
            df_municipio = df_otros[df_otros['municipio_sede_prestador'] == municipio]
            
            municipio_stats = {
                'municipio': municipio,
                'prestadores': df_municipio['nombre_prestador'].nunique(),
                'sedes': df_municipio['nombre_sede_prestador'].nunique(),
                'niveles_atencion': list(df_municipio['nivel_atencion_limpio'].unique())
            }
            
            # Por tipo de servicio
            for tipo_servicio in self.mapeo_servicios.keys():
                df_servicio = df_municipio[df_municipio['tipo_servicio'] == tipo_servicio]
                
                capacidad = int(df_servicio['cantidad_ci_TOTAL_REPS'].sum())
                ocupacion = int(df_servicio['total_ingresos_paciente_servicio'].sum())
                disponible = int(df_servicio['disponible'].sum())
                
                municipio_stats[f'{tipo_servicio}_capacidad'] = capacidad
                municipio_stats[f'{tipo_servicio}_ocupacion'] = ocupacion
                municipio_stats[f'{tipo_servicio}_disponible'] = disponible
                municipio_stats[f'{tipo_servicio}_porcentaje'] = round(
                    (ocupacion / capacidad * 100) if capacidad > 0 else 0, 1
                )
            
            # Totales del municipio
            municipio_stats['total_capacidad'] = int(df_municipio['cantidad_ci_TOTAL_REPS'].sum())
            municipio_stats['total_ocupacion'] = int(df_municipio['total_ingresos_paciente_servicio'].sum())
            municipio_stats['total_disponible'] = int(df_municipio['disponible'].sum())
            municipio_stats['total_porcentaje'] = round(
                (municipio_stats['total_ocupacion'] / municipio_stats['total_capacidad'] * 100)
                if municipio_stats['total_capacidad'] > 0 else 0, 1
            )
            
            stats_municipios.append(municipio_stats)
        
        return sorted(stats_municipios, key=lambda x: x['total_capacidad'], reverse=True)
    
    def mostrar_debug_clasificacion(self):
        """Función de debugging para mostrar cómo se están clasificando los tipos de capacidad."""
        if self.df is None:
            print("❌ No hay datos cargados para mostrar debug")
            return
        
        print("🔍" + "="*80)
        print("   DEBUG: ANÁLISIS DE CLASIFICACIÓN POR TIPOS DE SERVICIO")
        print("="*82)
        
        # Mostrar keywords usadas
        print("📋 KEYWORDS UTILIZADAS PARA CLASIFICACIÓN:")
        for tipo_servicio, info in self.mapeo_servicios.items():
            print(f"   🔹 {info['nombre'].upper()}:")
            keywords_str = ", ".join(info['keywords'])
            print(f"      Keywords: {keywords_str}")
        print()
        
        # Mostrar tipos únicos y su clasificación
        print("📊 TIPOS DE CAPACIDAD Y SU CLASIFICACIÓN:")
        tipos_clasificacion = []
        
        for tipo in sorted(self.df['nombre_capacidad_instalada'].unique()):
            clasificacion = self._clasificar_servicio(tipo)
            capacidad = self.df[self.df['nombre_capacidad_instalada'] == tipo]['cantidad_ci_TOTAL_REPS'].sum()
            ocupacion = self.df[self.df['nombre_capacidad_instalada'] == tipo]['total_ingresos_paciente_servicio'].sum()
            
            tipos_clasificacion.append({
                'tipo': tipo,
                'clasificacion': clasificacion,
                'capacidad': capacidad,
                'ocupacion': ocupacion
            })
        
        # Agrupar por clasificación
        for servicio in ['observacion', 'cuidado_critico', 'hospitalizacion']:
            tipos_servicio = [t for t in tipos_clasificacion if t['clasificacion'] == servicio]
            
            if tipos_servicio:
                print(f"   🔹 {self.mapeo_servicios[servicio]['nombre'].upper()}:")
                for tipo in tipos_servicio:
                    print(f"      • {tipo['tipo']} → Cap: {tipo['capacidad']}, Ocup: {tipo['ocupacion']}")
            else:
                print(f"   ❌ {self.mapeo_servicios[servicio]['nombre'].upper()}: SIN DATOS")
        
        print("="*82)
        
        # Sugerencias para observación si está vacía
        obs_data = self.df[self.df['tipo_servicio'] == 'observacion']
        if obs_data.empty:
            print("💡 SUGERENCIAS PARA OBSERVACIÓN/URGENCIAS:")
            print("   Si no se están clasificando correctamente los tipos de observación,")
            print("   revise estos tipos que podrían ser observación:")
            
            posibles_obs = []
            for tipo in self.df['nombre_capacidad_instalada'].unique():
                tipo_lower = tipo.lower()
                if any(word in tipo_lower for word in ['camilla', 'consulta', 'proced', 'emerg']):
                    posibles_obs.append(tipo)
            
            for tipo in posibles_obs[:10]:
                print(f"      • {tipo}")
            print()
    
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
        elementos.append(Paragraph("Análisis por Tipos de Servicio y Niveles de Atención", titulo_seccion))
        
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
        • Capacidad total instalada: {stats_tolima['general']['capacidad_total_departamento']:,} unidades<br/>
        • Ocupación actual: {stats_tolima['general']['ocupacion_total_departamento']:,} pacientes<br/>
        • Unidades disponibles: {stats_tolima['general']['disponible_total_departamento']:,}<br/>
        • Porcentaje de ocupación: {stats_tolima['general']['porcentaje_ocupacion_departamento']}%<br/><br/>
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
                • Capacidad instalada: {stats['capacidad_total']:,} unidades<br/>
                • Ocupación actual: {stats['ocupacion_total']:,} pacientes ({stats['porcentaje_ocupacion']}%)<br/>
                • Unidades disponibles: {stats['disponible']:,}<br/>
                • Municipios con este servicio: {stats['municipios']}<br/>
                • Prestadores: {stats['prestadores']} | Sedes: {stats['sedes']}<br/>
                • Estado: <i>{estado_desc}</i><br/><br/>
                """
                
                elementos.append(Paragraph(servicio_texto, texto_normal))
        
        # Estadísticas por nivel de atención
        elementos.append(Paragraph("🎯 <b>Análisis por Niveles de Atención</b>", titulo_subseccion))
        
        for nivel, info in self.mapeo_niveles.items():
            if nivel in stats_tolima['niveles']:
                stats = stats_tolima['niveles'][nivel]
                
                porcentaje = stats['porcentaje_ocupacion']
                if porcentaje >= UMBRALES['critico']:
                    estado = "🔴"
                elif porcentaje >= UMBRALES['advertencia']:
                    estado = "🟡"
                else:
                    estado = "🟢"
                
                nivel_texto = f"""
                <b>{estado} {info['nombre']} ({info['descripcion']})</b><br/>
                • Capacidad: {stats['capacidad_total']:,} unidades | Ocupación: {stats['ocupacion_total']:,} ({stats['porcentaje_ocupacion']}%)<br/>
                • Municipios: {stats['municipios']} | Prestadores: {stats['prestadores']}<br/>
                """
                
                elementos.append(Paragraph(nivel_texto, texto_normal))
        
        # Agregar información de N/A si existe
        if 'N/A' in stats_tolima['niveles']:
            stats = stats_tolima['niveles']['N/A']
            elementos.append(Paragraph(f"""
            <b>⚪ Sin Clasificar de Nivel</b><br/>
            • Capacidad: {stats['capacidad_total']:,} unidades | Ocupación: {stats['ocupacion_total']:,} ({stats['porcentaje_ocupacion']}%)<br/>
            • Municipios: {stats['municipios']} | Prestadores: {stats['prestadores']}<br/>
            """, texto_normal))
        
        elementos.append(PageBreak())
        
        # ======================================================================
        # 2. ANÁLISIS DETALLADO DE IBAGUÉ
        # ======================================================================
        elementos.append(Paragraph("2. ANÁLISIS DETALLADO - IBAGUÉ (CAPITAL)", titulo_seccion))
        
        stats_ibague = self._obtener_estadisticas_ibague()
        
        if stats_ibague:
            elementos.append(Paragraph("🏛️ <b>Ibagué como Centro de Referencia Departamental</b>", titulo_subseccion))
            
            # Calcular participación de Ibagué
            total_cap_ibague = stats_ibague['total']['capacidad_total']
            total_ocup_ibague = stats_ibague['total']['ocupacion_total']
            porcentaje_ibague = stats_ibague['total']['porcentaje_ocupacion']
            
            participacion_capacidad = round((total_cap_ibague / stats_tolima['general']['capacidad_total_departamento'] * 100), 1)
            participacion_ocupacion = round((total_ocup_ibague / stats_tolima['general']['ocupacion_total_departamento'] * 100), 1)
            
            resumen_ibague = f"""
            <b>Participación de Ibagué en el Sistema Departamental:</b><br/>
            • Participación en capacidad total: {participacion_capacidad}% del departamento<br/>
            • Participación en ocupación: {participacion_ocupacion}% del departamento<br/>
            • Capacidad total de Ibagué: {total_cap_ibague:,} unidades<br/>
            • Ocupación actual: {total_ocup_ibague:,} pacientes ({porcentaje_ibague}%)<br/>
            • Unidades disponibles: {stats_ibague['total']['disponible']:,}<br/>
            • Total de prestadores: {stats_ibague['total']['prestadores']}<br/>
            • Total de sedes: {stats_ibague['total']['sedes']}<br/><br/>
            """
            
            elementos.append(Paragraph(resumen_ibague, texto_normal))
            
            # Análisis por servicio en Ibagué
            elementos.append(Paragraph("📋 <b>Detalle por Tipo de Servicio en Ibagué</b>", titulo_subseccion))
            
            for tipo_servicio, info in self.mapeo_servicios.items():
                if tipo_servicio in stats_ibague:
                    stats = stats_ibague[tipo_servicio]
                    
                    participacion_servicio = round((stats['capacidad_total'] / total_cap_ibague * 100), 1) if total_cap_ibague > 0 else 0
                    
                    # Estado del servicio
                    porcentaje = stats['porcentaje_ocupacion']
                    if porcentaje >= UMBRALES['critico']:
                        estado = "🔴 CRÍTICO"
                    elif porcentaje >= UMBRALES['advertencia']:
                        estado = "🟡 ADVERTENCIA"
                    else:
                        estado = "🟢 NORMAL"
                    
                    servicio_ibague = f"""
                    <b>{info['nombre']} - {estado}</b><br/>
                    • Prestadores: {stats['prestadores']} | Sedes: {stats['sedes']}<br/>
                    • Capacidad: {stats['capacidad_total']:,} unidades ({participacion_servicio}% del total de Ibagué)<br/>
                    • Ocupación: {stats['ocupacion_total']:,} pacientes ({stats['porcentaje_ocupacion']}%)<br/>
                    • Disponibles: {stats['disponible']:,} unidades<br/><br/>
                    """
                    
                    elementos.append(Paragraph(servicio_ibague, texto_normal))
        
        elementos.append(PageBreak())
        
        # ======================================================================
        # 2.1. ANÁLISIS ESPECÍFICO DEL HOSPITAL FEDERICO LLERAS ACOSTA
        # ======================================================================
        elementos.append(Paragraph("2.1. ANÁLISIS ESPECÍFICO - HOSPITAL FEDERICO LLERAS ACOSTA", titulo_seccion))
        
        stats_federico = self._obtener_estadisticas_federico_lleras()
        
        if stats_federico:
            elementos.append(Paragraph("🏥 <b>Hospital Federico Lleras Acosta - Centro de Referencia Departamental</b>", titulo_subseccion))
            
            # Información general del Federico Lleras
            total_cap_federico = stats_federico['total']['capacidad_total']
            total_ocup_federico = stats_federico['total']['ocupacion_total']
            porcentaje_federico = stats_federico['total']['porcentaje_ocupacion']
            
            # Calcular participación respecto al total departamental
            participacion_federico_dept = round((total_cap_federico / stats_tolima['general']['capacidad_total_departamento'] * 100), 1)
            
            # Calcular participación respecto a Ibagué (si existe)
            participacion_federico_ibague = 0
            if stats_ibague:
                participacion_federico_ibague = round((total_cap_federico / stats_ibague['total']['capacidad_total'] * 100), 1)
            
            resumen_federico = f"""
            <b>Posicionamiento del Hospital Federico Lleras Acosta:</b><br/>
            • Participación en capacidad departamental: {participacion_federico_dept}% del total del Tolima<br/>"""
            
            if stats_ibague:
                resumen_federico += f"• Participación en capacidad de Ibagué: {participacion_federico_ibague}% del total de la capital<br/>"
            
            resumen_federico += f"""• Capacidad total: {total_cap_federico:,} unidades hospitalarias<br/>
            • Ocupación actual: {total_ocup_federico:,} pacientes ({porcentaje_federico}%)<br/>
            • Unidades disponibles: {stats_federico['total']['disponible']:,}<br/>
            • Número de sedes: {stats_federico['total']['sedes']}<br/>
            • Municipios donde opera: {stats_federico['total']['municipios']}<br/>
            • Tipos de capacidad diferentes: {stats_federico['total']['tipos_capacidad']}<br/><br/>
            """
            
            elementos.append(Paragraph(resumen_federico, texto_normal))
            
            # Análisis por servicio en el Federico Lleras
            elementos.append(Paragraph("📋 <b>Detalle por Tipo de Servicio - Federico Lleras</b>", titulo_subseccion))
            
            for tipo_servicio, info in self.mapeo_servicios.items():
                if tipo_servicio in stats_federico and stats_federico[tipo_servicio]['capacidad_total'] > 0:
                    stats = stats_federico[tipo_servicio]
                    
                    participacion_servicio = round((stats['capacidad_total'] / total_cap_federico * 100), 1) if total_cap_federico > 0 else 0
                    
                    # Estado del servicio
                    porcentaje = stats['porcentaje_ocupacion']
                    if porcentaje >= UMBRALES['critico']:
                        estado = "🔴 CRÍTICO"
                    elif porcentaje >= UMBRALES['advertencia']:
                        estado = "🟡 ADVERTENCIA"
                    else:
                        estado = "🟢 NORMAL"
                    
                    servicio_federico = f"""
                    <b>{info['nombre']} - {estado}</b><br/>
                    • Sedes con este servicio: {stats['sedes']}<br/>
                    • Capacidad: {stats['capacidad_total']:,} unidades ({participacion_servicio}% del total del hospital)<br/>
                    • Ocupación: {stats['ocupacion_total']:,} pacientes ({stats['porcentaje_ocupacion']}%)<br/>
                    • Disponibles: {stats['disponible']:,} unidades<br/>
                    • Tipos de capacidad: {stats['tipos_capacidad']}<br/><br/>
                    """
                    
                    elementos.append(Paragraph(servicio_federico, texto_normal))
        else:
            elementos.append(Paragraph("⚠️ <b>Hospital Federico Lleras Acosta no encontrado en los datos</b>", titulo_subseccion))
            elementos.append(Paragraph("No se pudo localizar el Hospital Federico Lleras Acosta en los datos proporcionados. Verifique el nombre del prestador en el archivo de datos.", texto_normal))
        
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
            porcentaje_otros = round((total_otros_ocup / total_otros_cap * 100), 1) if total_otros_cap > 0 else 0
            
            municipios_criticos = [m for m in stats_otros if m['total_porcentaje'] >= UMBRALES['critico']]
            municipios_advertencia = [m for m in stats_otros if UMBRALES['advertencia'] <= m['total_porcentaje'] < UMBRALES['critico']]
            
            resumen_otros = f"""
            <b>Panorama de Municipios (Excluyendo Ibagué):</b><br/>
            • Total de municipios analizados: {len(stats_otros)}<br/>
            • Capacidad total combinada: {total_otros_cap:,} unidades<br/>
            • Ocupación total: {total_otros_ocup:,} pacientes ({porcentaje_otros}%)<br/>
            • Municipios en estado crítico (≥90%): {len(municipios_criticos)}<br/>
            • Municipios en advertencia (70-89%): {len(municipios_advertencia)}<br/><br/>
            """
            
            elementos.append(Paragraph(resumen_otros, texto_normal))
            
            # Alertas críticas
            if municipios_criticos:
                elementos.append(Paragraph("🚨 <b>MUNICIPIOS EN ESTADO CRÍTICO</b>", titulo_subseccion))
                
                for municipio in municipios_criticos:
                    alerta_texto = f"""
                    <b>{municipio['municipio']}</b> - {municipio['total_porcentaje']}% de ocupación<br/>
                    • Capacidad: {municipio['total_capacidad']} | Ocupación: {municipio['total_ocupacion']}<br/>
                    • Prestadores: {municipio['prestadores']} | Sedes: {municipio['sedes']}<br/>
                    • Niveles de atención: {", ".join(municipio['niveles_atencion']) if municipio['niveles_atencion'] else "N/A"}<br/><br/>
                    """
                    elementos.append(Paragraph(alerta_texto, texto_normal))
        
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
        <b>Desarrollado por:</b> Ing. José Miguel Santos<br/>
        <b>Registros procesados:</b> {len(self.df):,} unidades de capacidad instalada
        """
        elementos.append(Paragraph(pie_texto, texto_normal))
        
        # Construir documento
        try:
            doc.build(elementos)
            print(f"✅ Informe PDF generado exitosamente: {archivo_salida}")
            return archivo_salida
        except Exception as e:
            print(f"❌ Error generando PDF: {str(e)}")
            import traceback
            traceback.print_exc()
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
        servicios_criticos = []
        for tipo_servicio, info in self.mapeo_servicios.items():
            if tipo_servicio in stats_tolima:
                porcentaje = stats_tolima[tipo_servicio]['porcentaje_ocupacion']
                if porcentaje >= UMBRALES['critico']:
                    servicios_criticos.append(info['nombre'])
        
        if servicios_criticos:
            conclusiones.append(f"⚠️ <b>SERVICIOS CRÍTICOS:</b> {', '.join(servicios_criticos)} presentan ocupación crítica y requieren atención inmediata.")
        
        # Análisis por niveles de atención
        niveles_criticos = []
        for nivel, info in self.mapeo_niveles.items():
            if nivel in stats_tolima['niveles']:
                porcentaje = stats_tolima['niveles'][nivel]['porcentaje_ocupacion']
                if porcentaje >= UMBRALES['critico']:
                    niveles_criticos.append(info['nombre'])
        
        if niveles_criticos:
            conclusiones.append(f"🎯 <b>NIVELES CRÍTICOS:</b> {', '.join(niveles_criticos)} requieren refuerzo inmediato de recursos.")
        
        # Análisis de Ibagué
        if stats_ibague:
            total_cap_ibague = stats_ibague['total']['capacidad_total']
            participacion = round((total_cap_ibague / stats_tolima['general']['capacidad_total_departamento'] * 100), 1)
            conclusiones.append(f"🏛️ <b>PAPEL DE IBAGUÉ:</b> Como capital concentra el {participacion}% de la capacidad hospitalaria departamental, siendo el principal centro de referencia con {stats_ibague['total']['prestadores']} prestadores y {stats_ibague['total']['sedes']} sedes.")
        
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
            "<br/>📋 <b>RECOMENDACIONES INMEDIATAS:</b>",
            "• Activar protocolos de referencia y contrarreferencia entre municipios",
            "• Fortalecer la coordinación entre Ibagué y municipios periféricos",
            "• Implementar monitoreo en tiempo real de ocupación por servicios y niveles",
            "• Preparar planes de contingencia para redistribución de pacientes",
            "• Reforzar personal médico en servicios con mayor ocupación",
            "• Evaluar ampliación de capacidad en niveles de alta complejidad",
            "• Mejorar la clasificación de niveles de atención en prestadores sin clasificar"
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
        print("   python hospital_report.py <archivo_excel> --debug")
        print("")
        print("📊 EJEMPLOS:")
        print("   python hospital_report.py datos_hospitalarios.xlsx")
        print("   python hospital_report.py datos_hospitalarios.xlsx informe_tolima.pdf")
        print("   python hospital_report.py datos_hospitalarios.xlsx --debug")
        print("")
        print("🔧 CARACTERÍSTICAS PRINCIPALES:")
        print("   ✅ Análisis por tipos de servicio (Observación, Crítico, Hospitalización)")
        print("   ✅ Análisis por niveles de atención (I, II, III, IV)")
        print("   ✅ Estructura: Tolima → Ibagué → Federico Lleras → Otros Municipios")
        print("   ✅ Gráficos optimizados y proporcionales")
        print("   ✅ Tablas detalladas por prestador y sede")
        print("   ✅ Alertas automáticas por umbrales de ocupación")
        print("   ✅ Análisis específico del Hospital Federico Lleras Acosta")
        print("")
        print("🔍 MODO DEBUG:")
        print("   Usar --debug para ver cómo se clasifican los tipos de capacidad")
        print("   Útil para diagnosticar problemas de clasificación")
        print("")
        print("📋 COLUMNAS REQUERIDAS EN EL ARCHIVO EXCEL:")
        print("   • municipio_sede_prestador: Municipio del departamento")
        print("   • nombre_prestador: Prestador de salud")
        print("   • nivel_de_atencion_prestador: Nivel de complejidad")
        print("   • nombre_sede_prestador: Nombre de la sede")
        print("   • nombre_capacidad_instalada: Tipo de cama/camilla")
        print("   • cantidad_ci_TOTAL_REPS: Capacidad total")
        print("   • total_ingresos_paciente_servicio: Pacientes ingresados")
        return
    
    archivo_excel = sys.argv[1]
    
    # Verificar modo debug
    modo_debug = len(sys.argv) > 2 and sys.argv[2] == '--debug'
    archivo_salida = None if modo_debug else (sys.argv[2] if len(sys.argv) > 2 else None)
    
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
        
        # Modo debug
        if modo_debug:
            generador.mostrar_debug_clasificacion()
            return
        
        # Generar informe (versión simplificada por ahora)
        archivo_generado = generador.generar_informe_pdf(archivo_salida)
        
        if archivo_generado:
            print("🎉" + "="*70)
            print("✅ PROCESAMIENTO COMPLETADO")
            print(f"📄 Los datos fueron procesados correctamente")
            print(f"📊 Datos procesados: {len(generador.df):,} registros")
            print(f"🏥 Municipios: {generador.df['municipio_sede_prestador'].nunique()}")
            print(f"🏛️ Prestadores: {generador.df['nombre_prestador'].nunique()}")
            print(f"📍 Sedes: {generador.df['nombre_sede_prestador'].nunique()}")
            print(f"🎯 Servicios analizados: {list(generador.df['tipo_servicio'].unique())}")
            print(f"🔢 Niveles de atención: {list(generador.df['nivel_atencion_limpio'].unique())}")
            
            # Verificar si se encontró el Federico Lleras
            stats_federico = generador._obtener_estadisticas_federico_lleras()
            if stats_federico:
                print(f"🏥 Hospital Federico Lleras: ✅ ENCONTRADO ({stats_federico['total']['capacidad_total']:,} unidades)")
            else:
                print(f"🏥 Hospital Federico Lleras: ❌ NO ENCONTRADO")
            
            print("="*72)
            
            # Verificar si hay problemas con la clasificación
            obs_data = generador.df[generador.df['tipo_servicio'] == 'observacion']
            if obs_data.empty:
                print("⚠️  ADVERTENCIA: No se encontraron datos para Observación/Urgencias")
                print("   💡 Ejecute con --debug para diagnosticar: python hospital_report.py archivo.xlsx --debug")
        else:
            print("❌ Error al generar el informe.")
            
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()