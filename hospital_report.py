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

Estructura: Tolima → Ibagué → Otros Municipios

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
    
    def _crear_grafico_tolima_servicios(self):
        """Crear gráfico de servicios del departamento del Tolima."""
        try:
            stats = self._obtener_estadisticas_tolima()
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Análisis de Capacidad Hospitalaria - Departamento del Tolima', 
                        fontsize=16, fontweight='bold', color=COLORS['primary'])
            
            # ===============================================================
            # GRÁFICO 1: Capacidad vs Ocupación por Servicios
            # ===============================================================
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
            
            x = np.arange(len(servicios))
            width = 0.35
            
            bars1 = ax1.bar(x - width/2, capacidades, width, label='Capacidad Total', 
                          color=colores, alpha=0.7, edgecolor='black')
            bars2 = ax1.bar(x + width/2, ocupaciones, width, label='Ocupación Actual', 
                          color=colores, alpha=1.0, edgecolor='black')
            
            ax1.set_title('Capacidad vs Ocupación por Tipo de Servicio', fontweight='bold', fontsize=12)
            ax1.set_ylabel('Número de Unidades')
            ax1.set_xticks(x)
            ax1.set_xticklabels(servicios, rotation=0, fontsize=10)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Agregar valores en las barras
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + max(capacidades) * 0.01,
                           f'{int(height)}', ha='center', va='bottom', fontweight='bold', fontsize=9)
            
            for bar in bars2:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + max(capacidades) * 0.01,
                           f'{int(height)}', ha='center', va='bottom', fontweight='bold', fontsize=9)
            
            # ===============================================================
            # GRÁFICO 2: Porcentajes de Ocupación por Servicios
            # ===============================================================
            bars3 = ax2.bar(servicios, porcentajes, color=colores, alpha=0.8, edgecolor='black')
            
            ax2.set_title('Porcentaje de Ocupación por Tipo de Servicio', fontweight='bold', fontsize=12)
            ax2.set_ylabel('Porcentaje de Ocupación (%)')
            ax2.set_xticklabels(servicios, rotation=0, fontsize=10)
            ax2.set_ylim(0, 100)
            
            # Líneas de referencia
            ax2.axhline(y=UMBRALES['advertencia'], color='orange', linestyle='--', alpha=0.7, label='Advertencia (70%)')
            ax2.axhline(y=UMBRALES['critico'], color='red', linestyle='--', alpha=0.7, label='Crítico (90%)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Agregar valores y colorear según umbral
            for i, (bar, porcentaje) in enumerate(zip(bars3, porcentajes)):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
                       f'{porcentaje}%', ha='center', va='bottom', fontweight='bold', fontsize=10)
                
                # Colorear borde según umbral
                if porcentaje >= UMBRALES['critico']:
                    bar.set_edgecolor('red')
                    bar.set_linewidth(3)
                elif porcentaje >= UMBRALES['advertencia']:
                    bar.set_edgecolor('orange')
                    bar.set_linewidth(2)
            
            # ===============================================================
            # GRÁFICO 3: Capacidad por Niveles de Atención
            # ===============================================================
            niveles = []
            cap_niveles = []
            colores_niveles = []
            
            for nivel, info in self.mapeo_niveles.items():
                if nivel in stats['niveles']:
                    niveles.append(info['nombre'])
                    cap_niveles.append(stats['niveles'][nivel]['capacidad_total'])
                    colores_niveles.append(info['color'])
            
            # Agregar N/A si existe
            if 'N/A' in stats['niveles']:
                niveles.append('Sin Clasificar')
                cap_niveles.append(stats['niveles']['N/A']['capacidad_total'])
                colores_niveles.append(COLORS['dark_gray'])
            
            bars4 = ax3.bar(niveles, cap_niveles, color=colores_niveles, alpha=0.8, edgecolor='black')
            
            ax3.set_title('Capacidad por Nivel de Atención', fontweight='bold', fontsize=12)
            ax3.set_ylabel('Capacidad Total')
            ax3.set_xticklabels(niveles, rotation=0, fontsize=10)
            ax3.grid(True, alpha=0.3)
            
            # Agregar valores
            for bar in bars4:
                height = bar.get_height()
                if height > 0:
                    ax3.text(bar.get_x() + bar.get_width()/2., height + max(cap_niveles) * 0.01,
                           f'{int(height)}', ha='center', va='bottom', fontweight='bold', fontsize=9)
            
            # ===============================================================
            # GRÁFICO 4: Ocupación por Niveles de Atención
            # ===============================================================
            ocup_niveles = []
            porc_niveles = []
            
            for nivel in niveles:
                if nivel == 'Sin Clasificar':
                    if 'N/A' in stats['niveles']:
                        ocup_niveles.append(stats['niveles']['N/A']['ocupacion_total'])
                        porc_niveles.append(stats['niveles']['N/A']['porcentaje_ocupacion'])
                    else:
                        ocup_niveles.append(0)
                        porc_niveles.append(0)
                else:
                    # Encontrar el nivel correspondiente
                    nivel_key = None
                    for k, v in self.mapeo_niveles.items():
                        if v['nombre'] == nivel:
                            nivel_key = k
                            break
                    
                    if nivel_key and nivel_key in stats['niveles']:
                        ocup_niveles.append(stats['niveles'][nivel_key]['ocupacion_total'])
                        porc_niveles.append(stats['niveles'][nivel_key]['porcentaje_ocupacion'])
                    else:
                        ocup_niveles.append(0)
                        porc_niveles.append(0)
            
            bars5 = ax4.bar(niveles, porc_niveles, color=colores_niveles, alpha=0.8, edgecolor='black')
            
            ax4.set_title('Porcentaje de Ocupación por Nivel de Atención', fontweight='bold', fontsize=12)
            ax4.set_ylabel('Porcentaje de Ocupación (%)')
            ax4.set_xticklabels(niveles, rotation=0, fontsize=10)
            ax4.set_ylim(0, 100)
            
            # Líneas de referencia
            ax4.axhline(y=UMBRALES['advertencia'], color='orange', linestyle='--', alpha=0.7)
            ax4.axhline(y=UMBRALES['critico'], color='red', linestyle='--', alpha=0.7)
            ax4.grid(True, alpha=0.3)
            
            # Agregar valores
            for bar, porcentaje in zip(bars5, porc_niveles):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 2,
                       f'{porcentaje}%', ha='center', va='bottom', fontweight='bold', fontsize=9)
                
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
            import traceback
            traceback.print_exc()
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
            
            # ===============================================================
            # GRÁFICO 1: Capacidad vs Ocupación por Servicios
            # ===============================================================
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
            
            x = np.arange(len(servicios))
            width = 0.35
            
            bars1 = ax1.bar(x - width/2, capacidades, width, label='Capacidad', 
                          color=colores, alpha=0.7, edgecolor='black')
            bars2 = ax1.bar(x + width/2, ocupaciones, width, label='Ocupación', 
                          color=colores, alpha=1.0, edgecolor='black')
            
            ax1.set_title('Capacidad vs Ocupación por Servicio', fontweight='bold')
            ax1.set_ylabel('Número de Unidades')
            ax1.set_xticks(x)
            ax1.set_xticklabels(servicios, rotation=0, fontsize=10)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Valores en barras
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + max(capacidades) * 0.02,
                           f'{int(height)}', ha='center', va='bottom', fontsize=10)
            
            for bar in bars2:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + max(capacidades) * 0.02,
                           f'{int(height)}', ha='center', va='bottom', fontsize=10)
            
            # ===============================================================
            # GRÁFICO 2: Porcentajes de Ocupación por Servicios
            # ===============================================================
            bars3 = ax2.bar(servicios, porcentajes, color=colores, alpha=0.8, edgecolor='black')
            ax2.set_title('Porcentaje de Ocupación por Servicio', fontweight='bold')
            ax2.set_ylabel('Porcentaje (%)')
            ax2.set_xticklabels(servicios, rotation=0, fontsize=10)
            ax2.set_ylim(0, 100)
            ax2.axhline(y=70, color='orange', linestyle='--', alpha=0.7)
            ax2.axhline(y=90, color='red', linestyle='--', alpha=0.7)
            ax2.grid(True, alpha=0.3)
            
            for bar, porcentaje in zip(bars3, porcentajes):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
                       f'{porcentaje}%', ha='center', va='bottom', fontsize=10)
            
            # ===============================================================
            # GRÁFICO 3: Prestadores por Servicio
            # ===============================================================
            prestadores_data = [stats[tipo]['prestadores'] for tipo in self.mapeo_servicios.keys()]
            
            ax3.bar(servicios, prestadores_data, color=colores, alpha=0.8, edgecolor='black')
            ax3.set_title('Número de Prestadores por Servicio', fontweight='bold')
            ax3.set_ylabel('Número de Prestadores')
            ax3.set_xticklabels(servicios, rotation=0, fontsize=10)
            ax3.grid(True, alpha=0.3)
            
            for i, v in enumerate(prestadores_data):
                ax3.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
            
            # ===============================================================
            # GRÁFICO 4: Capacidad por Niveles de Atención en Ibagué
            # ===============================================================
            niveles_ibague = []
            cap_niveles_ibague = []
            colores_niveles_ibague = []
            
            for nivel, info in self.mapeo_niveles.items():
                if nivel in stats['niveles']:
                    niveles_ibague.append(info['nombre'])
                    cap_niveles_ibague.append(stats['niveles'][nivel]['capacidad_total'])
                    colores_niveles_ibague.append(info['color'])
            
            if 'N/A' in stats['niveles']:
                niveles_ibague.append('Sin Clasificar')
                cap_niveles_ibague.append(stats['niveles']['N/A']['capacidad_total'])
                colores_niveles_ibague.append(COLORS['dark_gray'])
            
            if niveles_ibague:  # Solo si hay datos
                ax4.bar(niveles_ibague, cap_niveles_ibague, color=colores_niveles_ibague, alpha=0.8, edgecolor='black')
                ax4.set_title('Capacidad por Nivel de Atención', fontweight='bold')
                ax4.set_ylabel('Capacidad Total')
                ax4.set_xticklabels(niveles_ibague, rotation=0, fontsize=10)
                ax4.grid(True, alpha=0.3)
                
                for i, v in enumerate(cap_niveles_ibague):
                    if v > 0:
                        ax4.text(i, v + max(cap_niveles_ibague) * 0.02, str(v), ha='center', va='bottom', fontweight='bold')
            else:
                ax4.text(0.5, 0.5, 'Sin datos de niveles\npara Ibagué', ha='center', va='center', 
                        transform=ax4.transAxes, fontsize=12)
                ax4.set_title('Capacidad por Nivel de Atención', fontweight='bold')
            
            plt.tight_layout()
            plt.savefig('grafico_ibague_detallado.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            return 'grafico_ibague_detallado.png'
            
        except Exception as e:
            print(f"❌ Error creando gráfico de Ibagué: {str(e)}")
            import traceback
            traceback.print_exc()
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
                          color=COLORS['secondary'], alpha=0.7, edgecolor='black')
            bars2 = ax1.bar(x + width/2, ocupaciones, width, label='Ocupación Actual', 
                          color=COLORS['primary'], alpha=0.8, edgecolor='black')
            
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
                    ax1.text(bar.get_x() + bar.get_width()/2., height + max(capacidades) * 0.01,
                           f'{int(height)}', ha='center', va='bottom', fontsize=8)
            
            # Gráfico 2: Porcentajes de Ocupación
            bars3 = ax2.bar(municipios, porcentajes, alpha=0.8, edgecolor='black')
            
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
                       f'{porcentaje}%', ha='center', va='bottom', fontsize=8)
            
            ax2.set_title('Porcentaje de Ocupación por Municipio', fontweight='bold')
            ax2.set_ylabel('Porcentaje de Ocupación (%)')
            ax2.set_xlabel('Municipio')
            ax2.set_xticklabels(municipios, rotation=45, ha='right')
            ax2.set_ylim(0, 100)
            
            # Líneas de referencia
            ax2.axhline(y=UMBRALES['advertencia'], color='orange', linestyle='--', alpha=0.7, label='Advertencia (70%)')
            ax2.axhline(y=UMBRALES['critico'], color='red', linestyle='--', alpha=0.7, label='Crítico (90%)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('grafico_otros_municipios.png', dpi=300, bbox_inches='tight')
            plt.close()
            
    def _crear_grafico_federico_lleras(self):
        """Crear gráfico detallado específico del Hospital Federico Lleras Acosta."""
        try:
            stats = self._obtener_estadisticas_federico_lleras()
            if not stats:
                return None
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'Análisis Detallado - Hospital Federico Lleras Acosta', 
                        fontsize=16, fontweight='bold', color=COLORS['primary'])
            
            # ===============================================================
            # GRÁFICO 1: Capacidad vs Ocupación por Servicios
            # ===============================================================
            servicios = []
            capacidades = []
            ocupaciones = []
            porcentajes = []
            colores = []
            
            for tipo_servicio, info in self.mapeo_servicios.items():
                if tipo_servicio in stats and stats[tipo_servicio]['capacidad_total'] > 0:
                    servicios.append(info['nombre'])
                    capacidades.append(stats[tipo_servicio]['capacidad_total'])
                    ocupaciones.append(stats[tipo_servicio]['ocupacion_total'])
                    porcentajes.append(stats[tipo_servicio]['porcentaje_ocupacion'])
                    colores.append(info['color'])
            
            if servicios:  # Solo si hay datos
                x = np.arange(len(servicios))
                width = 0.35
                
                bars1 = ax1.bar(x - width/2, capacidades, width, label='Capacidad', 
                              color=colores, alpha=0.7, edgecolor='black')
                bars2 = ax1.bar(x + width/2, ocupaciones, width, label='Ocupación', 
                              color=colores, alpha=1.0, edgecolor='black')
                
                ax1.set_title('Capacidad vs Ocupación por Servicio', fontweight='bold')
                ax1.set_ylabel('Número de Unidades')
                ax1.set_xticks(x)
                ax1.set_xticklabels(servicios, rotation=0, fontsize=10)
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Valores en barras
                for bar in bars1:
                    height = bar.get_height()
                    if height > 0:
                        ax1.text(bar.get_x() + bar.get_width()/2., height + max(capacidades) * 0.02,
                               f'{int(height)}', ha='center', va='bottom', fontsize=10)
                
                for bar in bars2:
                    height = bar.get_height()
                    if height > 0:
                        ax1.text(bar.get_x() + bar.get_width()/2., height + max(capacidades) * 0.02,
                               f'{int(height)}', ha='center', va='bottom', fontsize=10)
            else:
                ax1.text(0.5, 0.5, 'Sin datos de servicios\ndisponibles', ha='center', va='center', 
                        transform=ax1.transAxes, fontsize=12)
                ax1.set_title('Capacidad vs Ocupación por Servicio', fontweight='bold')
            
            # ===============================================================
            # GRÁFICO 2: Porcentajes de Ocupación por Servicios
            # ===============================================================
            if servicios:
                bars3 = ax2.bar(servicios, porcentajes, color=colores, alpha=0.8, edgecolor='black')
                ax2.set_title('Porcentaje de Ocupación por Servicio', fontweight='bold')
                ax2.set_ylabel('Porcentaje (%)')
                ax2.set_xticklabels(servicios, rotation=0, fontsize=10)
                ax2.set_ylim(0, 100)
                ax2.axhline(y=70, color='orange', linestyle='--', alpha=0.7)
                ax2.axhline(y=90, color='red', linestyle='--', alpha=0.7)
                ax2.grid(True, alpha=0.3)
                
                for bar, porcentaje in zip(bars3, porcentajes):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
                           f'{porcentaje}%', ha='center', va='bottom', fontsize=10)
            else:
                ax2.text(0.5, 0.5, 'Sin datos de ocupación\ndisponibles', ha='center', va='center', 
                        transform=ax2.transAxes, fontsize=12)
                ax2.set_title('Porcentaje de Ocupación por Servicio', fontweight='bold')
            
            # ===============================================================
            # GRÁFICO 3: Capacidad por Sedes
            # ===============================================================
            if stats['sedes']:
                sedes_nombres = [sede['nombre'][:20] + '...' if len(sede['nombre']) > 20 else sede['nombre'] 
                               for sede in stats['sedes']]
                sedes_capacidades = [sede['capacidad_total'] for sede in stats['sedes']]
                sedes_ocupaciones = [sede['ocupacion_total'] for sede in stats['sedes']]
                
                x_sedes = np.arange(len(sedes_nombres))
                width = 0.35
                
                ax3.bar(x_sedes - width/2, sedes_capacidades, width, label='Capacidad', 
                       color=COLORS['secondary'], alpha=0.7, edgecolor='black')
                ax3.bar(x_sedes + width/2, sedes_ocupaciones, width, label='Ocupación', 
                       color=COLORS['primary'], alpha=0.8, edgecolor='black')
                
                ax3.set_title('Capacidad por Sede', fontweight='bold')
                ax3.set_ylabel('Número de Unidades')
                ax3.set_xticks(x_sedes)
                ax3.set_xticklabels(sedes_nombres, rotation=45, ha='right', fontsize=9)
                ax3.legend()
                ax3.grid(True, alpha=0.3)
            else:
                ax3.text(0.5, 0.5, 'Sin datos de sedes\ndisponibles', ha='center', va='center', 
                        transform=ax3.transAxes, fontsize=12)
                ax3.set_title('Capacidad por Sede', fontweight='bold')
            
            # ===============================================================
            # GRÁFICO 4: Capacidad por Niveles de Atención
            # ===============================================================
            niveles_federico = []
            cap_niveles_federico = []
            colores_niveles_federico = []
            
            for nivel, info in self.mapeo_niveles.items():
                if nivel in stats['niveles'] and stats['niveles'][nivel]['capacidad_total'] > 0:
                    niveles_federico.append(info['nombre'])
                    cap_niveles_federico.append(stats['niveles'][nivel]['capacidad_total'])
                    colores_niveles_federico.append(info['color'])
            
            if 'N/A' in stats['niveles'] and stats['niveles']['N/A']['capacidad_total'] > 0:
                niveles_federico.append('Sin Clasificar')
                cap_niveles_federico.append(stats['niveles']['N/A']['capacidad_total'])
                colores_niveles_federico.append(COLORS['dark_gray'])
            
            if niveles_federico:  # Solo si hay datos
                ax4.bar(niveles_federico, cap_niveles_federico, color=colores_niveles_federico, alpha=0.8, edgecolor='black')
                ax4.set_title('Capacidad por Nivel de Atención', fontweight='bold')
                ax4.set_ylabel('Capacidad Total')
                ax4.set_xticklabels(niveles_federico, rotation=0, fontsize=10)
                ax4.grid(True, alpha=0.3)
                
                for i, v in enumerate(cap_niveles_federico):
                    if v > 0:
                        ax4.text(i, v + max(cap_niveles_federico) * 0.02, str(v), ha='center', va='bottom', fontweight='bold')
            else:
                ax4.text(0.5, 0.5, 'Sin datos de niveles\ndisponibles', ha='center', va='center', 
                        transform=ax4.transAxes, fontsize=12)
                ax4.set_title('Capacidad por Nivel de Atención', fontweight='bold')
            
            plt.tight_layout()
            plt.savefig('grafico_federico_lleras.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            return 'grafico_federico_lleras.png'
            
        except Exception as e:
            print(f"❌ Error creando gráfico del Federico Lleras: {str(e)}")
            import traceback
            traceback.print_exc()
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
            'Nivel',
            'Observación\nCap/Ocup/%',
            'Cuidado Crítico\nCap/Ocup/%',
            'Hospitalización\nCap/Ocup/%',
            'Total\nCap/Ocup/%'
        ]
        
        # Datos por prestador
        for prestador in df_ibague['nombre_prestador'].unique():
            df_prestador = df_ibague[df_ibague['nombre_prestador'] == prestador]
            
            # Obtener nivel predominante del prestador
            nivel_prestador = df_prestador['nivel_atencion_limpio'].mode().iloc[0] if len(df_prestador['nivel_atencion_limpio'].mode()) > 0 else 'N/A'
            
            # Fila del prestador (totales)
            prestador_row = [f"🏥 {prestador[:40]}{'...' if len(prestador) > 40 else ''}", nivel_prestador]
            
            total_cap = 0
            total_ocup = 0
            
            for tipo_servicio in ['observacion', 'cuidado_critico', 'hospitalizacion']:
                df_servicio = df_prestador[df_prestador['tipo_servicio'] == tipo_servicio]
                cap = int(df_servicio['cantidad_ci_TOTAL_REPS'].sum())
                ocup = int(df_servicio['total_ingresos_paciente_servicio'].sum())
                perc = round((ocup / cap * 100), 1) if cap > 0 else 0
                
                if cap > 0:
                    prestador_row.append(f"{cap}/{ocup}/{perc}%")
                else:
                    prestador_row.append("-")
                
                total_cap += cap
                total_ocup += ocup
            
            total_perc = round((total_ocup / total_cap * 100), 1) if total_cap > 0 else 0
            if total_cap > 0:
                prestador_row.append(f"{total_cap}/{total_ocup}/{total_perc}%")
            else:
                prestador_row.append("-")
            
            tabla_data.append(prestador_row)
            
            # Filas por sede (solo si hay más de una sede)
            sedes = df_prestador['nombre_sede_prestador'].unique()
            if len(sedes) > 1:
                for sede in sedes:
                    df_sede = df_prestador[df_prestador['nombre_sede_prestador'] == sede]
                    
                    # Obtener nivel de la sede
                    nivel_sede = df_sede['nivel_atencion_limpio'].mode().iloc[0] if len(df_sede['nivel_atencion_limpio'].mode()) > 0 else 'N/A'
                    
                    sede_row = [f"  └─ {sede[:35]}{'...' if len(sede) > 35 else ''}", nivel_sede]
                    
                    sede_cap = 0
                    sede_ocup = 0
                    
                    for tipo_servicio in ['observacion', 'cuidado_critico', 'hospitalizacion']:
                        df_servicio = df_sede[df_sede['tipo_servicio'] == tipo_servicio]
                        cap = int(df_servicio['cantidad_ci_TOTAL_REPS'].sum())
                        ocup = int(df_servicio['total_ingresos_paciente_servicio'].sum())
                        perc = round((ocup / cap * 100), 1) if cap > 0 else 0
                        
                        if cap > 0:
                            sede_row.append(f"{cap}/{ocup}/{perc}%")
                        else:
                            sede_row.append("-")
                        
                        sede_cap += cap
                        sede_ocup += ocup
                    
                    sede_perc = round((sede_ocup / sede_cap * 100), 1) if sede_cap > 0 else 0
                    if sede_cap > 0:
                        sede_row.append(f"{sede_cap}/{sede_ocup}/{sede_perc}%")
                    else:
                        sede_row.append("-")
                    
                    tabla_data.append(sede_row)
        
    def _crear_tabla_detallada_federico_lleras(self):
        """Crear tabla detallada del Hospital Federico Lleras Acosta."""
        stats = self._obtener_estadisticas_federico_lleras()
        
        if not stats:
            return None
        
        tabla_data = []
        
        # Encabezados
        headers = [
            'Sede/Servicio',
            'Municipio',
            'Nivel',
            'Observación\nCap/Ocup/%',
            'Cuidado Crítico\nCap/Ocup/%',
            'Hospitalización\nCap/Ocup/%',
            'Total\nCap/Ocup/%',
            'Estado'
        ]
        
        # Datos por sede
        for sede_stats in stats['sedes']:
            # Determinar estado según porcentaje
            porcentaje = sede_stats['porcentaje_ocupacion']
            if porcentaje >= UMBRALES['critico']:
                estado = "🔴 CRÍTICO"
            elif porcentaje >= UMBRALES['advertencia']:
                estado = "🟡 ADVERTENCIA"
            else:
                estado = "🟢 NORMAL"
            
            sede_row = [
                f"🏢 {sede_stats['nombre'][:30]}{'...' if len(sede_stats['nombre']) > 30 else ''}",
                sede_stats['municipio'],
                sede_stats['nivel'],
                f"{sede_stats['observacion_capacidad']}/{sede_stats['observacion_ocupacion']}/{sede_stats['observacion_porcentaje']}%" if sede_stats['observacion_capacidad'] > 0 else "-",
                f"{sede_stats['cuidado_critico_capacidad']}/{sede_stats['cuidado_critico_ocupacion']}/{sede_stats['cuidado_critico_porcentaje']}%" if sede_stats['cuidado_critico_capacidad'] > 0 else "-",
                f"{sede_stats['hospitalizacion_capacidad']}/{sede_stats['hospitalizacion_ocupacion']}/{sede_stats['hospitalizacion_porcentaje']}%" if sede_stats['hospitalizacion_capacidad'] > 0 else "-",
                f"{sede_stats['capacidad_total']}/{sede_stats['ocupacion_total']}/{sede_stats['porcentaje_ocupacion']}%",
                estado
            ]
            
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
            'Niveles',
            'Observación\nCap/Ocup/%',
            'Cuidado Crítico\nCap/Ocup/%',
            'Hospitalización\nCap/Ocup/%',
            'Total General\nCap/Ocup/%',
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
            
            # Formatear niveles de atención
            niveles_text = ", ".join(sorted([n for n in municipio_stats['niveles_atencion'] if n != 'N/A']))
            if not niveles_text:
                niveles_text = "N/A"
            
            fila = [
                municipio_stats['municipio'],
                str(municipio_stats['prestadores']),
                str(municipio_stats['sedes']),
                niveles_text,
                f"{municipio_stats['observacion_capacidad']}/{municipio_stats['observacion_ocupacion']}/{municipio_stats['observacion_porcentaje']}%" if municipio_stats['observacion_capacidad'] > 0 else "-",
                f"{municipio_stats['cuidado_critico_capacidad']}/{municipio_stats['cuidado_critico_ocupacion']}/{municipio_stats['cuidado_critico_porcentaje']}%" if municipio_stats['cuidado_critico_capacidad'] > 0 else "-",
                f"{municipio_stats['hospitalizacion_capacidad']}/{municipio_stats['hospitalizacion_ocupacion']}/{municipio_stats['hospitalizacion_porcentaje']}%" if municipio_stats['hospitalizacion_capacidad'] > 0 else "-",
                f"{municipio_stats['total_capacidad']}/{municipio_stats['total_ocupacion']}/{municipio_stats['total_porcentaje']}%",
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
        elementos.append(Paragraph("Análisis por Tipos de Servicio y Niveles de Atención", titulo_seccion))
        
        elementos.append(Spacer(1, 0.5*inch))
        
        fecha_str = self.fecha_procesamiento.strftime("%d de %B de %Y")
        elementos.append(Paragraph(f"<b>Fecha de Procesamiento:</b> {fecha_str}", texto_normal))
        elementos.append(Paragraph(f"<b>Secretaría de Salud del Tolima</b>", texto_normal))
        elementos.append(Paragraph(f"<b>Sistema de Monitoreo Hospitalario</b>", texto_normal))
        
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
            
            # Análisis por niveles de atención en Federico Lleras
            if 'niveles' in stats_federico and stats_federico['niveles']:
                elementos.append(Paragraph("🎯 <b>Distribución por Niveles de Atención - Federico Lleras</b>", titulo_subseccion))
                
                for nivel, info in self.mapeo_niveles.items():
                    if nivel in stats_federico['niveles'] and stats_federico['niveles'][nivel]['capacidad_total'] > 0:
                        stats = stats_federico['niveles'][nivel]
                        
                        porcentaje = stats['porcentaje_ocupacion']
                        if porcentaje >= UMBRALES['critico']:
                            estado = "🔴"
                        elif porcentaje >= UMBRALES['advertencia']:
                            estado = "🟡"
                        else:
                            estado = "🟢"
                        
                        nivel_federico = f"""
                        <b>{estado} {info['nombre']} ({info['descripcion']})</b><br/>
                        • Capacidad: {stats['capacidad_total']:,} | Ocupación: {stats['ocupacion_total']:,} ({stats['porcentaje_ocupacion']}%)<br/>
                        • Sedes: {stats['sedes']} | Tipos de capacidad: {stats['tipos_capacidad']}<br/>
                        """
                        
                        elementos.append(Paragraph(nivel_federico, texto_normal))
                
                if 'N/A' in stats_federico['niveles'] and stats_federico['niveles']['N/A']['capacidad_total'] > 0:
                    stats = stats_federico['niveles']['N/A']
                    elementos.append(Paragraph(f"""
                    <b>⚪ Sin Clasificar de Nivel</b><br/>
                    • Capacidad: {stats['capacidad_total']:,} | Ocupación: {stats['ocupacion_total']:,} ({stats['porcentaje_ocupacion']}%)<br/>
                    • Sedes: {stats['sedes']} | Tipos de capacidad: {stats['tipos_capacidad']}<br/>
                    """, texto_normal))
            
            # Gráfico detallado del Federico Lleras
            grafico_federico = self._crear_grafico_federico_lleras()
            if grafico_federico and os.path.exists(grafico_federico):
                elementos.append(Spacer(1, 0.2*inch))
                elementos.append(Image(grafico_federico, width=7*inch, height=5.5*inch))
                elementos.append(Spacer(1, 0.2*inch))
            
            # Tabla detallada del Federico Lleras
            tabla_federico = self._crear_tabla_detallada_federico_lleras()
            if tabla_federico:
                elementos.append(Paragraph("📊 <b>Tabla Detallada por Sede - Hospital Federico Lleras</b>", titulo_subseccion))
                
                # Crear tabla para PDF
                tabla_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['danger'])),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 7),
                    ('FONTSIZE', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ])
                
                # Colorear filas según estado
                for i, fila in enumerate(tabla_federico[1:], 1):
                    if "CRÍTICO" in fila[-1]:
                        tabla_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FFEBEE'))
                    elif "ADVERTENCIA" in fila[-1]:
                        tabla_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FFF3E0'))
                
                tabla_pdf = Table(tabla_federico, repeatRows=1)
                tabla_pdf.setStyle(tabla_style)
                elementos.append(tabla_pdf)
        else:
            elementos.append(Paragraph("⚠️ <b>Hospital Federico Lleras Acosta no encontrado en los datos</b>", titulo_subseccion))
            elementos.append(Paragraph("No se pudo localizar el Hospital Federico Lleras Acosta en los datos proporcionados. Verifique el nombre del prestador en el archivo de datos.", texto_normal))
        
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
        
        # Gráfico del Tolima
        grafico_tolima = self._crear_grafico_tolima_servicios()
        if grafico_tolima and os.path.exists(grafico_tolima):
            elementos.append(Spacer(1, 0.2*inch))
            elementos.append(Image(grafico_tolima, width=7*inch, height=5.5*inch))
            elementos.append(Spacer(1, 0.2*inch))
        
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
            
            # Análisis por niveles de atención en Ibagué
            if 'niveles' in stats_ibague and stats_ibague['niveles']:
                elementos.append(Paragraph("🎯 <b>Distribución por Niveles de Atención en Ibagué</b>", titulo_subseccion))
                
                for nivel, info in self.mapeo_niveles.items():
                    if nivel in stats_ibague['niveles']:
                        stats = stats_ibague['niveles'][nivel]
                        
                        nivel_ibague = f"""
                        <b>{info['nombre']} ({info['descripcion']})</b><br/>
                        • Capacidad: {stats['capacidad_total']:,} | Ocupación: {stats['ocupacion_total']:,} ({stats['porcentaje_ocupacion']}%)<br/>
                        • Prestadores: {stats['prestadores']} | Sedes: {stats['sedes']}<br/>
                        """
                        
                        elementos.append(Paragraph(nivel_ibague, texto_normal))
                
                if 'N/A' in stats_ibague['niveles']:
                    stats = stats_ibague['niveles']['N/A']
                    elementos.append(Paragraph(f"""
                    <b>Sin Clasificar de Nivel</b><br/>
                    • Capacidad: {stats['capacidad_total']:,} | Ocupación: {stats['ocupacion_total']:,} ({stats['porcentaje_ocupacion']}%)<br/>
                    • Prestadores: {stats['prestadores']} | Sedes: {stats['sedes']}<br/>
                    """, texto_normal))
            
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
                    ('FONTSIZE', (0, 0), (-1, 0), 6),
                    ('FONTSIZE', (0, 1), (-1, -1), 5),
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
        
        # Generar informe
        archivo_generado = generador.generar_informe_pdf(archivo_salida)
        
        if archivo_generado:
            print("🎉" + "="*70)
            print("✅ INFORME GENERADO EXITOSAMENTE")
            print(f"📄 Archivo: {archivo_generado}")
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
            print("🔍 ESTRUCTURA DEL INFORME:")
            print("   1. Resumen Ejecutivo del Tolima (por servicios y niveles)")
            print("   2. Análisis Detallado de Ibagué (centro de referencia)")
            print("   2.1. Análisis Específico del Hospital Federico Lleras Acosta")
            print("   3. Análisis de Otros Municipios (comparativo)")
            print("   4. Conclusiones y Recomendaciones (automáticas)")
            print("="*72)
            
            # Sugerir modo debug si hay problemas
            obs_data = generador.df[generador.df['tipo_servicio'] == 'observacion']
            if obs_data.empty:
                print("⚠️  ADVERTENCIA: No se encontraron datos para Observación/Urgencias")
                print("   💡 Ejecute con --debug para diagnosticar: python hospital_report.py archivo.xlsx --debug")
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
            'grafico_federico_lleras.png',
            'grafico_otros_municipios.png'
        ]
        
        for archivo in archivos_temp:
            if os.path.exists(archivo):
                try:
                    os.remove(archivo)
                except:
                    pass
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
        print("🔧 CARACTERÍSTICAS PRINCIPALES:")
        print("   ✅ Análisis por tipos de servicio (Observación, Crítico, Hospitalización)")
        print("   ✅ Análisis por niveles de atención (I, II, III, IV)")
        print("   ✅ Estructura: Tolima → Ibagué → Otros Municipios")
        print("   ✅ Gráficos optimizados y proporcionales")
        print("   ✅ Tablas detalladas por prestador y sede")
        print("   ✅ Alertas automáticas por umbrales de ocupación")
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
            print(f"📊 Datos procesados: {len(generador.df):,} registros")
            print(f"🏥 Municipios: {generador.df['municipio_sede_prestador'].nunique()}")
            print(f"🏛️ Prestadores: {generador.df['nombre_prestador'].nunique()}")
            print(f"📍 Sedes: {generador.df['nombre_sede_prestador'].nunique()}")
            print(f"🎯 Servicios analizados: {list(generador.df['tipo_servicio'].unique())}")
            print(f"🔢 Niveles de atención: {list(generador.df['nivel_atencion_limpio'].unique())}")
            print("="*72)
            print("🔍 ESTRUCTURA DEL INFORME:")
            print("   1. Resumen Ejecutivo del Tolima (por servicios y niveles)")
            print("   2. Análisis Detallado de Ibagué (centro de referencia)")
            print("   2.1. Análisis Específico del Hospital Federico Lleras Acosta")
            print("   3. Análisis de Otros Municipios (comparativo)")
            print("   4. Conclusiones y Recomendaciones (automáticas)")
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
            'grafico_federico_lleras.png',
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