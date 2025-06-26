#!/usr/bin/env python3
"""
Generador de Informe Final Optimizado de Capacidad Hospitalaria
VERSIÓN DEFINITIVA CON MÁXIMAS MEJORAS VISUALES Y DE DETALLE
Secretaría de Salud del Tolima

MEJORAS FINALES:
- Alertas críticas en formato TABLA (mejor visual)
- CAMAS vs CAMILLAS distinguidas en TODOS los análisis
- Análisis detallado por MUNICIPIO + PRESTADOR específico
- Gráficos más altos verticalmente para mejor visualización
- Tablas optimizadas con mejor estructura visual

Desarrollado por: Ing. José Miguel Santos
Para: Secretaría de Salud del Tolima
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Importaciones de ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Colores institucionales Secretaría de Salud del Tolima
COLORS = {
    "primary": "#7D0F2B",      # Rojo institucional
    "secondary": "#F2A900",     # Amarillo dorado
    "accent": "#5A4214",        # Marrón
    "success": "#509E2F",       # Verde
    "warning": "#F7941D",       # Naranja
    "white": "#FFFFFF",         # Blanco
}

def procesar_datos_final_optimizado(archivo_excel):
    """Procesa datos con distinción completa CAMAS/CAMILLAS en todos los análisis"""
    print("📊 Procesando datos con optimización final...")
    
    # Leer Excel
    df = pd.read_excel(archivo_excel)
    
    # Limpiar datos numéricos
    columnas_numericas = [
        'cantidad_ci_TOTAL_REPS', 
        'ocupacion_ci_confirmado_covid19',
        'ocupacion_ci_sospechoso_covid19', 
        'ocupacion_ci_no_covid19',
        'cantidad_ci_disponibles',
        'total_ingresos_paciente_servicio'
    ]
    
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Usar la columna correcta para ocupación
    df['ocupacion_total'] = df['total_ingresos_paciente_servicio']
    
    # Calcular porcentaje de ocupación
    df['porcentaje_ocupacion'] = np.where(
        df['cantidad_ci_TOTAL_REPS'] > 0,
        (df['ocupacion_total'] / df['cantidad_ci_TOTAL_REPS']) * 100, 
        0
    )
    
    # Limpiar y estandarizar nombres
    df['municipio_sede_prestador'] = df['municipio_sede_prestador'].str.upper().str.strip()
    df['nombre_prestador'] = df['nombre_prestador'].str.strip()
    df['nombre_sede_prestador'] = df['nombre_sede_prestador'].str.strip()
    df['nombre_capacidad_instalada'] = df['nombre_capacidad_instalada'].str.strip()
    
    # CLASIFICACIÓN PRINCIPAL: CAMAS vs CAMILLAS (para usar en TODOS los análisis)
    def clasificar_cama_camilla(nombre):
        nombre = str(nombre).upper()
        if 'CAMA' in nombre:
            return 'CAMAS'
        elif 'CAMILLA' in nombre:
            return 'CAMILLAS'
        else:
            return 'OTROS'
    
    df['tipo_general'] = df['nombre_capacidad_instalada'].apply(clasificar_cama_camilla)
    
    # CLASIFICACIÓN ESPECÍFICA con identificación CAMAS/CAMILLAS
    def categorizar_capacidad_con_tipo(nombre):
        nombre = str(nombre).upper()
        tipo_base = "CAMAS" if 'CAMA' in nombre else "CAMILLAS" if 'CAMILLA' in nombre else "OTROS"
        
        if 'CAMA' in nombre and 'INTENSIV' in nombre and 'ADULT' in nombre:
            return f'{tipo_base} - UCI Adultos'
        elif 'CAMA' in nombre and 'INTENSIV' in nombre and 'PEDIÁTRIC' in nombre:
            return f'{tipo_base} - UCI Pediátrica'
        elif 'CAMA' in nombre and 'INTERMEDI' in nombre and 'ADULT' in nombre:
            return f'{tipo_base} - Cuidado Intermedio Adultos'
        elif 'CAMA' in nombre and 'INTERMEDI' in nombre and 'PEDIÁTRIC' in nombre:
            return f'{tipo_base} - Cuidado Intermedio Pediátrico'
        elif 'CAMA' in nombre and 'ADULT' in nombre:
            return f'{tipo_base} - Hospitalización Adultos'
        elif 'CAMA' in nombre and 'PEDIÁTRIC' in nombre:
            return f'{tipo_base} - Hospitalización Pediátrica'
        elif 'CAMILLA' in nombre and 'OBSERVACIÓN' in nombre and 'ADULT' in nombre and 'HOMBRE' in nombre:
            return f'{tipo_base} - Observación Adultos Hombres'
        elif 'CAMILLA' in nombre and 'OBSERVACIÓN' in nombre and 'ADULT' in nombre and 'MUJER' in nombre:
            return f'{tipo_base} - Observación Adultos Mujeres'
        elif 'CAMILLA' in nombre and 'OBSERVACIÓN' in nombre and 'PEDIÁTRIC' in nombre:
            return f'{tipo_base} - Observación Pediátrica'
        else:
            return f'{tipo_base} - {nombre}'
    
    df['categoria_con_tipo'] = df['nombre_capacidad_instalada'].apply(categorizar_capacidad_con_tipo)
    
    # Para mantener compatibilidad
    df['categoria_especifica'] = df['categoria_con_tipo'].str.split(' - ').str[1]
    
    # Crear identificadores únicos
    df['prestador_sede'] = df['nombre_prestador'] + " - " + df['nombre_sede_prestador']
    df['sede_id'] = df['nombre_prestador'] + "_" + df['numero_sede'].astype(str)
    
    # Tipo de institución
    df['tipo_institucion'] = df['naturaleza_juridica'].apply(
        lambda x: 'Pública' if 'Pública' in str(x) else 'Privada'
    )
    
    print(f"✅ Datos procesados: {len(df)} registros")
    print(f"   📍 {df['municipio_sede_prestador'].nunique()} municipios")
    print(f"   🏥 {df['nombre_prestador'].nunique()} prestadores")
    print(f"   🏢 {df['sede_id'].nunique()} sedes")
    print(f"   🛏️  CAMAS: {len(df[df['tipo_general'] == 'CAMAS'])}, CAMILLAS: {len(df[df['tipo_general'] == 'CAMILLAS'])}")
    print(f"   📋 {df['categoria_con_tipo'].nunique()} tipos específicos (con distinción CAMAS/CAMILLAS)")
    
    return df

def calcular_estadisticas_optimizadas(df):
    """Calcula estadísticas con distinción CAMAS/CAMILLAS en todos los análisis"""
    print("📈 Calculando estadísticas optimizadas...")
    
    fecha = df['fecha_registro'].dropna().iloc[0] if not df['fecha_registro'].dropna().empty else "N/A"
    
    # ===== 1. RESUMEN GENERAL CAMAS vs CAMILLAS =====
    resumen_camas_camillas = df.groupby('tipo_general').agg({
        'cantidad_ci_TOTAL_REPS': 'sum',
        'ocupacion_total': 'sum',
        'cantidad_ci_disponibles': 'sum',
        'municipio_sede_prestador': 'nunique',
        'nombre_prestador': 'nunique',
        'sede_id': 'nunique'
    }).reset_index()
    
    resumen_camas_camillas['porcentaje_ocupacion'] = np.where(
        resumen_camas_camillas['cantidad_ci_TOTAL_REPS'] > 0,
        (resumen_camas_camillas['ocupacion_total'] / resumen_camas_camillas['cantidad_ci_TOTAL_REPS']) * 100,
        0
    )
    
    # ===== 2. ANÁLISIS POR TIPOS ESPECÍFICOS CON DISTINCIÓN CAMAS/CAMILLAS =====
    capacidad_con_tipo = df.groupby('categoria_con_tipo').agg({
        'cantidad_ci_TOTAL_REPS': 'sum',
        'ocupacion_total': 'sum',
        'cantidad_ci_disponibles': 'sum',
        'municipio_sede_prestador': 'nunique',
        'nombre_prestador': 'nunique',
        'sede_id': 'nunique'
    }).reset_index()
    
    capacidad_con_tipo['porcentaje_ocupacion'] = np.where(
        capacidad_con_tipo['cantidad_ci_TOTAL_REPS'] > 0,
        (capacidad_con_tipo['ocupacion_total'] / capacidad_con_tipo['cantidad_ci_TOTAL_REPS']) * 100,
        0
    )
    
    capacidad_con_tipo = capacidad_con_tipo.sort_values('cantidad_ci_TOTAL_REPS', ascending=False)
    
    # ===== 3. RESUMEN TERRITORIAL COMPLETO =====
    tolima_general = {
        'capacidad': int(df['cantidad_ci_TOTAL_REPS'].sum()),
        'ocupada': int(df['ocupacion_total'].sum()),
        'disponible': int(df['cantidad_ci_disponibles'].sum()),
        'porcentaje': round((df['ocupacion_total'].sum() / df['cantidad_ci_TOTAL_REPS'].sum() * 100), 1) 
                     if df['cantidad_ci_TOTAL_REPS'].sum() > 0 else 0
    }
    
    # TODOS los municipios
    municipios_completo = df.groupby('municipio_sede_prestador').agg({
        'cantidad_ci_TOTAL_REPS': 'sum',
        'ocupacion_total': 'sum',
        'cantidad_ci_disponibles': 'sum',
        'nombre_prestador': 'nunique',
        'sede_id': 'nunique',
        'categoria_con_tipo': 'nunique'
    }).reset_index()
    
    municipios_completo.rename(columns={
        'nombre_prestador': 'num_prestadores',
        'sede_id': 'num_sedes',
        'categoria_con_tipo': 'tipos_capacidad'
    }, inplace=True)
    
    municipios_completo['porcentaje_ocupacion'] = np.where(
        municipios_completo['cantidad_ci_TOTAL_REPS'] > 0,
        (municipios_completo['ocupacion_total'] / municipios_completo['cantidad_ci_TOTAL_REPS']) * 100,
        0
    )
    
    municipios_completo = municipios_completo.sort_values('cantidad_ci_TOTAL_REPS', ascending=False)
    
    # ===== 4. ANÁLISIS DETALLADO POR PRESTADOR (DENTRO DE MUNICIPIOS) =====
    prestadores_detallado = df.groupby(['municipio_sede_prestador', 'nombre_prestador', 'tipo_institucion']).agg({
        'cantidad_ci_TOTAL_REPS': 'sum',
        'ocupacion_total': 'sum',
        'cantidad_ci_disponibles': 'sum',
        'sede_id': 'nunique',
        'categoria_con_tipo': 'nunique'
    }).reset_index()
    
    prestadores_detallado.rename(columns={
        'sede_id': 'num_sedes',
        'categoria_con_tipo': 'tipos_capacidad'
    }, inplace=True)
    
    prestadores_detallado['porcentaje_ocupacion'] = np.where(
        prestadores_detallado['cantidad_ci_TOTAL_REPS'] > 0,
        (prestadores_detallado['ocupacion_total'] / prestadores_detallado['cantidad_ci_TOTAL_REPS']) * 100,
        0
    )
    
    # ===== 5. MATRIZ MUNICIPIO × TIPO CON CAMAS/CAMILLAS =====
    matriz_municipio_tipo = df.groupby(['municipio_sede_prestador', 'categoria_con_tipo']).agg({
        'cantidad_ci_TOTAL_REPS': 'sum',
        'ocupacion_total': 'sum',
        'cantidad_ci_disponibles': 'sum',
        'nombre_prestador': 'nunique',
        'sede_id': 'nunique'
    }).reset_index()
    
    matriz_municipio_tipo['porcentaje_ocupacion'] = np.where(
        matriz_municipio_tipo['cantidad_ci_TOTAL_REPS'] > 0,
        (matriz_municipio_tipo['ocupacion_total'] / matriz_municipio_tipo['cantidad_ci_TOTAL_REPS']) * 100,
        0
    )
    
    # ===== 6. SEDES ESPECÍFICAS DETALLADAS =====
    sedes_detallado = df.groupby([
        'municipio_sede_prestador', 'nombre_prestador', 'nombre_sede_prestador', 
        'numero_sede', 'categoria_con_tipo', 'tipo_institucion'
    ]).agg({
        'cantidad_ci_TOTAL_REPS': 'sum',
        'ocupacion_total': 'sum',
        'cantidad_ci_disponibles': 'sum'
    }).reset_index()
    
    sedes_detallado['porcentaje_ocupacion'] = np.where(
        sedes_detallado['cantidad_ci_TOTAL_REPS'] > 0,
        (sedes_detallado['ocupacion_total'] / sedes_detallado['cantidad_ci_TOTAL_REPS']) * 100,
        0
    )
    
    # ===== 7. IDENTIFICAR ALERTAS CRÍTICAS =====
    municipios_criticos = municipios_completo[municipios_completo['porcentaje_ocupacion'] >= 90]
    
    prestadores_criticos = prestadores_detallado[prestadores_detallado['porcentaje_ocupacion'] >= 90]
    
    sedes_criticas = sedes_detallado[sedes_detallado['porcentaje_ocupacion'] >= 90].sort_values('porcentaje_ocupacion', ascending=False)
    
    tipos_criticos = capacidad_con_tipo[capacidad_con_tipo['porcentaje_ocupacion'] >= 90]
    
    municipio_tipo_critico = matriz_municipio_tipo[matriz_municipio_tipo['porcentaje_ocupacion'] >= 90]
    
    # ===== 8. IBAGUÉ DETALLADO =====
    ibague_general = municipios_completo[municipios_completo['municipio_sede_prestador'] == 'IBAGUÉ'].iloc[0].to_dict() if len(municipios_completo[municipios_completo['municipio_sede_prestador'] == 'IBAGUÉ']) > 0 else {}
    
    ibague_por_tipo = matriz_municipio_tipo[
        matriz_municipio_tipo['municipio_sede_prestador'] == 'IBAGUÉ'
    ].sort_values('cantidad_ci_TOTAL_REPS', ascending=False)
    
    # ===== 9. ANÁLISIS INSTITUCIONAL =====
    instituciones_resumen = df.groupby('tipo_institucion').agg({
        'cantidad_ci_TOTAL_REPS': 'sum',
        'ocupacion_total': 'sum',
        'cantidad_ci_disponibles': 'sum',
        'municipio_sede_prestador': 'nunique',
        'nombre_prestador': 'nunique'
    }).reset_index()
    
    instituciones_resumen['porcentaje_ocupacion'] = np.where(
        instituciones_resumen['cantidad_ci_TOTAL_REPS'] > 0,
        (instituciones_resumen['ocupacion_total'] / instituciones_resumen['cantidad_ci_TOTAL_REPS']) * 100,
        0
    )
    
    print("✅ Estadísticas optimizadas calculadas")
    
    return {
        'fecha': fecha,
        
        # RESUMEN GENERAL
        'tolima_general': tolima_general,
        'resumen_camas_camillas': resumen_camas_camillas,
        
        # TERRITORIAL COMPLETO
        'municipios_completo': municipios_completo,
        'prestadores_detallado': prestadores_detallado,  # NUEVO: Detalle por prestador
        'municipios_criticos': municipios_criticos,
        'ibague_general': ibague_general,
        
        # ANÁLISIS POR TIPO CON CAMAS/CAMILLAS
        'capacidad_con_tipo': capacidad_con_tipo,  # MEJORADO: Con distinción CAMAS/CAMILLAS
        'tipos_criticos': tipos_criticos,
        
        # MATRICES CRUZADAS
        'matriz_municipio_tipo': matriz_municipio_tipo,
        'ibague_por_tipo': ibague_por_tipo,
        
        # SEDES Y ALERTAS
        'sedes_detallado': sedes_detallado,
        'sedes_criticas': sedes_criticas,
        'prestadores_criticos': prestadores_criticos,  # NUEVO
        'municipio_tipo_critico': municipio_tipo_critico,
        
        # ANÁLISIS INSTITUCIONAL
        'instituciones_resumen': instituciones_resumen,
        
        # DATOS RAW
        'df': df
    }

def crear_graficos_optimizados_verticales(stats):
    """Crea gráficos optimizados con mayor altura vertical"""
    print("📊 Creando gráficos optimizados con mayor altura...")
    
    plt.style.use('default')
    plt.rcParams['font.size'] = 12  # Aumentar fuente
    
    # ===== GRÁFICO 1: CAMAS vs CAMILLAS (MÁS ALTO) =====
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))  # Vertical más alto
    
    camas_camillas = stats['resumen_camas_camillas']
    
    # Capacidad total CAMAS vs CAMILLAS
    bars1 = ax1.bar(camas_camillas['tipo_general'], camas_camillas['cantidad_ci_TOTAL_REPS'],
                    color=[COLORS['primary'], COLORS['secondary']], alpha=0.8, edgecolor='black', width=0.6)
    ax1.set_ylabel('Capacidad Total', fontsize=16)
    ax1.set_title('CAPACIDAD TOTAL: CAMAS vs CAMILLAS', fontweight='bold', fontsize=18)
    ax1.grid(True, alpha=0.3)
    
    for bar, valor in zip(bars1, camas_camillas['cantidad_ci_TOTAL_REPS']):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(camas_camillas['cantidad_ci_TOTAL_REPS']) * 0.02,
                f'{int(valor):,}', ha='center', va='bottom', fontweight='bold', fontsize=16)
    
    # Ocupación CAMAS vs CAMILLAS
    bars2 = ax2.bar(camas_camillas['tipo_general'], camas_camillas['porcentaje_ocupacion'],
                    color=[COLORS['accent'], COLORS['warning']], alpha=0.8, edgecolor='black', width=0.6)
    ax2.set_ylabel('Porcentaje de Ocupación (%)', fontsize=16)
    ax2.set_title('OCUPACIÓN: CAMAS vs CAMILLAS', fontweight='bold', fontsize=18)
    ax2.set_ylim(0, 100)
    ax2.axhline(y=90, color='red', linestyle='--', alpha=0.7, label='Crítico (90%)', linewidth=3)
    ax2.grid(True, alpha=0.3)
    
    for bar, valor in zip(bars2, camas_camillas['porcentaje_ocupacion']):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 3,
                f'{valor:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=16)
    
    ax2.legend(fontsize=14)
    plt.tight_layout()
    plt.savefig('grafico1_camas_camillas_alto.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # ===== GRÁFICO 2: MUNICIPIOS PRINCIPALES (MÁS ALTO) =====
    fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(18, 16))  # Más alto y ancho
    
    top_municipios = stats['municipios_completo'].head(15)  # Top 15
    
    # Capacidad por municipio
    bars3 = ax3.bar(range(len(top_municipios)), top_municipios['cantidad_ci_TOTAL_REPS'],
                    color=[COLORS['secondary'] if mun == 'IBAGUÉ' else COLORS['primary'] 
                          for mun in top_municipios['municipio_sede_prestador']], 
                    alpha=0.8, edgecolor='black')
    
    ax3.set_ylabel('Capacidad Total', fontsize=16)
    ax3.set_title('CAPACIDAD HOSPITALARIA POR MUNICIPIO (Top 15)', fontweight='bold', fontsize=18)
    ax3.set_xticks(range(len(top_municipios)))
    ax3.set_xticklabels(top_municipios['municipio_sede_prestador'], rotation=45, ha='right', fontsize=13)
    ax3.grid(True, alpha=0.3)
    
    for bar, valor in zip(bars3, top_municipios['cantidad_ci_TOTAL_REPS']):
        ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(top_municipios['cantidad_ci_TOTAL_REPS']) * 0.01,
                f'{int(valor):,}', ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Ocupación por municipio
    bars4 = ax4.bar(range(len(top_municipios)), top_municipios['porcentaje_ocupacion'],
                    color=[COLORS['warning'] if x >= 90 else COLORS['success'] if x < 70 else COLORS['primary'] 
                          for x in top_municipios['porcentaje_ocupacion']], 
                    alpha=0.8, edgecolor='black')
    
    ax4.set_xlabel('Municipios', fontsize=16)
    ax4.set_ylabel('Porcentaje de Ocupación (%)', fontsize=16)
    ax4.set_title('OCUPACIÓN POR MUNICIPIO (Top 15)', fontweight='bold', fontsize=18)
    ax4.set_xticks(range(len(top_municipios)))
    ax4.set_xticklabels(top_municipios['municipio_sede_prestador'], rotation=45, ha='right', fontsize=13)
    ax4.set_ylim(0, 100)
    ax4.axhline(y=90, color='red', linestyle='--', alpha=0.7, label='Crítico (90%)', linewidth=3)
    ax4.grid(True, alpha=0.3)
    
    for bar, valor in zip(bars4, top_municipios['porcentaje_ocupacion']):
        ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                f'{valor:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    ax4.legend(fontsize=14)
    plt.tight_layout()
    plt.savefig('grafico2_municipios_alto.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # ===== GRÁFICO 3: TIPOS CON CAMAS/CAMILLAS (MÁS ALTO) =====
    fig3, (ax5, ax6) = plt.subplots(2, 1, figsize=(20, 16))  # Muy alto para todos los tipos
    
    cap_data = stats['capacidad_con_tipo'].head(12)  # Top 12
    colores_cap = [COLORS['primary'], COLORS['secondary'], COLORS['accent'], COLORS['success'], 
                  COLORS['warning']] * 3
    
    # Capacidad total por tipo con CAMAS/CAMILLAS
    bars5 = ax5.bar(range(len(cap_data)), cap_data['cantidad_ci_TOTAL_REPS'],
                    color=colores_cap[:len(cap_data)], alpha=0.8, edgecolor='black')
    ax5.set_ylabel('Capacidad Total', fontsize=16)
    ax5.set_title('CAPACIDAD POR TIPO (Con distinción CAMAS/CAMILLAS)', fontweight='bold', fontsize=18)
    ax5.set_xticks(range(len(cap_data)))
    ax5.set_xticklabels(cap_data['categoria_con_tipo'], rotation=45, ha='right', fontsize=11)
    ax5.grid(True, alpha=0.3)
    
    for bar, valor in zip(bars5, cap_data['cantidad_ci_TOTAL_REPS']):
        ax5.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(cap_data['cantidad_ci_TOTAL_REPS']) * 0.01,
                f'{int(valor):,}', ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Ocupación por tipo con CAMAS/CAMILLAS
    bars6 = ax6.bar(range(len(cap_data)), cap_data['porcentaje_ocupacion'],
                    color=[COLORS['warning'] if x >= 90 else COLORS['success'] if x < 70 else COLORS['primary'] 
                          for x in cap_data['porcentaje_ocupacion']], 
                    alpha=0.8, edgecolor='black')
    ax6.set_xlabel('Tipo de Capacidad (CAMAS/CAMILLAS)', fontsize=16)
    ax6.set_ylabel('Porcentaje de Ocupación (%)', fontsize=16)
    ax6.set_title('OCUPACIÓN POR TIPO (Con distinción CAMAS/CAMILLAS)', fontweight='bold', fontsize=18)
    ax6.set_xticks(range(len(cap_data)))
    ax6.set_xticklabels(cap_data['categoria_con_tipo'], rotation=45, ha='right', fontsize=11)
    ax6.set_ylim(0, 100)
    ax6.axhline(y=90, color='red', linestyle='--', alpha=0.7, label='Crítico (90%)', linewidth=3)
    ax6.grid(True, alpha=0.3)
    
    for bar, valor in zip(bars6, cap_data['porcentaje_ocupacion']):
        ax6.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                f'{valor:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    ax6.legend(fontsize=14)
    plt.tight_layout()
    plt.savefig('grafico3_tipos_camas_camillas_alto.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # ===== GRÁFICO 4: IBAGUÉ DETALLADO (MÁS ALTO) =====
    if len(stats['ibague_por_tipo']) > 0:
        fig4, (ax7, ax8) = plt.subplots(2, 1, figsize=(18, 14))  # Más alto
        
        ibague_data = stats['ibague_por_tipo']
        
        # Capacidad en Ibagué por tipo
        bars7 = ax7.bar(range(len(ibague_data)), ibague_data['cantidad_ci_TOTAL_REPS'],
                        color=COLORS['secondary'], alpha=0.8, edgecolor='black')
        ax7.set_ylabel('Capacidad Total', fontsize=16)
        ax7.set_title('CAPACIDAD EN IBAGUÉ POR TIPO (Con CAMAS/CAMILLAS)', fontweight='bold', fontsize=18)
        ax7.set_xticks(range(len(ibague_data)))
        ax7.set_xticklabels(ibague_data['categoria_con_tipo'], rotation=45, ha='right', fontsize=12)
        ax7.grid(True, alpha=0.3)
        
        for bar, valor in zip(bars7, ibague_data['cantidad_ci_TOTAL_REPS']):
            ax7.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(ibague_data['cantidad_ci_TOTAL_REPS']) * 0.02,
                    f'{int(valor)}', ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Ocupación en Ibagué por tipo
        bars8 = ax8.bar(range(len(ibague_data)), ibague_data['porcentaje_ocupacion'],
                        color=[COLORS['warning'] if x >= 90 else COLORS['success'] if x < 70 else COLORS['primary'] 
                              for x in ibague_data['porcentaje_ocupacion']], 
                        alpha=0.8, edgecolor='black')
        ax8.set_xlabel('Tipo de Capacidad (CAMAS/CAMILLAS)', fontsize=16)
        ax8.set_ylabel('Porcentaje de Ocupación (%)', fontsize=16)
        ax8.set_title('OCUPACIÓN EN IBAGUÉ POR TIPO (Con CAMAS/CAMILLAS)', fontweight='bold', fontsize=18)
        ax8.set_xticks(range(len(ibague_data)))
        ax8.set_xticklabels(ibague_data['categoria_con_tipo'], rotation=45, ha='right', fontsize=12)
        ax8.set_ylim(0, 100)
        ax8.axhline(y=90, color='red', linestyle='--', alpha=0.7, label='Crítico (90%)', linewidth=3)
        ax8.grid(True, alpha=0.3)
        
        for bar, valor in zip(bars8, ibague_data['porcentaje_ocupacion']):
            ax8.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                    f'{valor:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        ax8.legend(fontsize=14)
        plt.tight_layout()
        plt.savefig('grafico4_ibague_alto.png', dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
    
    print("✅ Gráficos optimizados con mayor altura creados")

def generar_pdf_final_optimizado(stats, archivo_salida):
    """Genera PDF final optimizado con alertas en tabla y máximo detalle"""
    print("📄 Generando PDF final optimizado...")
    
    doc = SimpleDocTemplate(archivo_salida, pagesize=A4, topMargin=0.4*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados mejorados
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=18, alignment=TA_CENTER, spaceAfter=25)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, spaceBefore=18)
    subheading_style = ParagraphStyle('CustomSubHeading', parent=styles['Heading3'], fontSize=11, spaceAfter=10)
    
    # ===== ENCABEZADO =====
    story.append(Paragraph("SECRETARÍA DE SALUD DEL TOLIMA", title_style))
    story.append(Paragraph("Informe Final Optimizado de Capacidad Hospitalaria", heading_style))
    story.append(Paragraph("Análisis Exhaustivo: CAMAS/CAMILLAS + Territorial + Prestadores + Sedes", subheading_style))
    story.append(Paragraph(f"Fecha del Reporte: {stats['fecha']}", styles['Normal']))
    story.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # ===== 1. RESUMEN EJECUTIVO OPTIMIZADO =====
    story.append(Paragraph("1. RESUMEN EJECUTIVO GENERAL", heading_style))
    
    # Tabla Tolima General mejorada
    story.append(Paragraph("1.1 Departamento del Tolima - Resumen General", subheading_style))
    tolima_data = [[
        'Indicador', 'Valor', 'Observaciones'
    ], [
        'Capacidad Total',
        f"{stats['tolima_general']['capacidad']:,}",
        f"Camas + Camillas disponibles"
    ], [
        'Ocupación Actual',
        f"{stats['tolima_general']['ocupada']:,}",
        f"{stats['tolima_general']['porcentaje']:.1f}% del total"
    ], [
        'Disponibles',
        f"{stats['tolima_general']['disponible']:,}",
        f"{100 - stats['tolima_general']['porcentaje']:.1f}% disponible"
    ]]
    
    tabla_tolima = Table(tolima_data)
    tabla_tolima.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), 'lightgrey'),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'black'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, 'black'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(tabla_tolima)
    story.append(Spacer(1, 15))
    
    # Tabla CAMAS vs CAMILLAS mejorada
    story.append(Paragraph("1.2 Análisis CAMAS vs CAMILLAS", subheading_style))
    camas_camillas_data = [['Tipo', 'Capacidad Total', 'Ocupada', 'Disponible', '% Ocupación', 'Municipios', 'Prestadores', 'Sedes']]
    
    for _, row in stats['resumen_camas_camillas'].iterrows():
        estado = "🔴" if row['porcentaje_ocupacion'] >= 90 else "🟡" if row['porcentaje_ocupacion'] >= 80 else "🟢"
        camas_camillas_data.append([
            f"{estado} {row['tipo_general']}",
            f"{int(row['cantidad_ci_TOTAL_REPS']):,}",
            f"{int(row['ocupacion_total']):,}",
            f"{int(row['cantidad_ci_disponibles']):,}",
            f"{row['porcentaje_ocupacion']:.1f}%",
            f"{int(row['municipio_sede_prestador'])}",
            f"{int(row['nombre_prestador'])}",
            f"{int(row['sede_id'])}"
        ])
    
    tabla_camas_camillas = Table(camas_camillas_data)
    tabla_camas_camillas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), 'lightblue'),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'black'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, 'black'),
    ]))
    
    story.append(tabla_camas_camillas)
    story.append(Spacer(1, 20))
    
    # ===== 2. GRÁFICOS OPTIMIZADOS (MÁS GRANDES) =====
    story.append(Paragraph("2. ANÁLISIS GRÁFICO OPTIMIZADO", heading_style))
    
    story.append(Paragraph("2.1 Capacidad y Ocupación: CAMAS vs CAMILLAS", subheading_style))
    story.append(Image('grafico1_camas_camillas_alto.png', width=8*inch, height=6*inch))  # Más alto
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("2.2 Análisis Municipal Detallado", subheading_style))
    story.append(Image('grafico2_municipios_alto.png', width=8.5*inch, height=7*inch))  # Más alto
    story.append(Spacer(1, 15))
    
    story.append(PageBreak())
    
    # ===== 3. ALERTAS CRÍTICAS EN FORMATO TABLA (MEJORADO) =====
    story.append(Paragraph("3. ALERTAS CRÍTICAS DETALLADAS", heading_style))
    
    alertas_encontradas = False
    
    # 3.1 MUNICIPIOS CRÍTICOS (TABLA)
    if len(stats['municipios_criticos']) > 0:
        story.append(Paragraph("3.1 🚨 MUNICIPIOS CON OCUPACIÓN CRÍTICA (≥90%)", subheading_style))
        
        municipios_criticos_data = [['Municipio', 'Prestadores', 'Sedes', 'Capacidad', 'Ocupada', '% Ocupación', 'Estado']]
        
        for _, mun in stats['municipios_criticos'].iterrows():
            municipios_criticos_data.append([
                mun['municipio_sede_prestador'],
                f"{int(mun['num_prestadores'])}",
                f"{int(mun['num_sedes'])}",
                f"{int(mun['cantidad_ci_TOTAL_REPS']):,}",
                f"{int(mun['ocupacion_total']):,}",
                f"{mun['porcentaje_ocupacion']:.1f}%",
                "🔴 CRÍTICO"
            ])
        
        tabla_municipios_criticos = Table(municipios_criticos_data)
        tabla_municipios_criticos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), 'lightcoral'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'black'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
        ]))
        
        story.append(tabla_municipios_criticos)
        story.append(Spacer(1, 15))
        alertas_encontradas = True
    
    # 3.2 SEDES ESPECÍFICAS CRÍTICAS (TABLA MEJORADA)
    if len(stats['sedes_criticas']) > 0:
        story.append(Paragraph("3.2 🚨 SEDES ESPECÍFICAS CON OCUPACIÓN CRÍTICA (≥90%)", subheading_style))
        
        sedes_criticas_data = [['Municipio', 'Prestador', 'Sede', 'Tipo Capacidad', 'Cap.', 'Ocup.', '% Ocup.', 'Tipo Inst.']]
        
        for _, sede in stats['sedes_criticas'].head(20).iterrows():  # Top 20 sedes críticas
            sedes_criticas_data.append([
                sede['municipio_sede_prestador'],
                sede['nombre_prestador'][:25] + "..." if len(sede['nombre_prestador']) > 25 else sede['nombre_prestador'],
                sede['nombre_sede_prestador'][:20] + "..." if len(sede['nombre_sede_prestador']) > 20 else sede['nombre_sede_prestador'],
                sede['categoria_con_tipo'][:15] + "..." if len(sede['categoria_con_tipo']) > 15 else sede['categoria_con_tipo'],
                f"{int(sede['cantidad_ci_TOTAL_REPS'])}",
                f"{int(sede['ocupacion_total'])}",
                f"{sede['porcentaje_ocupacion']:.1f}%",
                sede['tipo_institucion']
            ])
        
        tabla_sedes_criticas = Table(sedes_criticas_data)
        tabla_sedes_criticas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), 'orange'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'black'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
        ]))
        
        story.append(tabla_sedes_criticas)
        story.append(Spacer(1, 15))
        alertas_encontradas = True
    
    # 3.3 TIPOS DE CAPACIDAD CRÍTICOS (TABLA)
    if len(stats['tipos_criticos']) > 0:
        story.append(Paragraph("3.3 🚨 TIPOS DE CAPACIDAD CRÍTICOS EN TOLIMA (≥90%)", subheading_style))
        
        tipos_criticos_data = [['Tipo de Capacidad', 'Total', 'Ocupada', '% Ocupación', 'Municipios', 'Prestadores', 'Sedes']]
        
        for _, tipo in stats['tipos_criticos'].iterrows():
            tipos_criticos_data.append([
                tipo['categoria_con_tipo'],
                f"{int(tipo['cantidad_ci_TOTAL_REPS']):,}",
                f"{int(tipo['ocupacion_total']):,}",
                f"{tipo['porcentaje_ocupacion']:.1f}%",
                f"{int(tipo['municipio_sede_prestador'])}",
                f"{int(tipo['nombre_prestador'])}",
                f"{int(tipo['sede_id'])}"
            ])
        
        tabla_tipos_criticos = Table(tipos_criticos_data)
        tabla_tipos_criticos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), 'yellow'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'black'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
        ]))
        
        story.append(tabla_tipos_criticos)
        story.append(Spacer(1, 15))
        alertas_encontradas = True
    
    if not alertas_encontradas:
        story.append(Paragraph("✅ No se encontraron alertas críticas en el sistema.", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # ===== 4. ANÁLISIS POR TIPOS CON CAMAS/CAMILLAS =====
    story.append(Paragraph("4. ANÁLISIS POR TIPOS DE CAPACIDAD (CAMAS/CAMILLAS)", heading_style))
    
    story.append(Image('grafico3_tipos_camas_camillas_alto.png', width=8.5*inch, height=7*inch))  # Más alto
    story.append(Spacer(1, 15))
    
    # Tabla detallada de tipos con CAMAS/CAMILLAS
    story.append(Paragraph("4.1 Detalle por Tipo con Distinción CAMAS/CAMILLAS", subheading_style))
    tipos_data = [['Tipo de Capacidad', 'Total', 'Ocupada', '% Ocupación', 'Municipios', 'Prestadores', 'Sedes']]
    
    for _, row in stats['capacidad_con_tipo'].iterrows():
        estado = "🔴" if row['porcentaje_ocupacion'] >= 90 else "🟡" if row['porcentaje_ocupacion'] >= 80 else "🟢"
        tipos_data.append([
            f"{estado} {row['categoria_con_tipo']}",
            f"{int(row['cantidad_ci_TOTAL_REPS']):,}",
            f"{int(row['ocupacion_total']):,}",
            f"{row['porcentaje_ocupacion']:.1f}%",
            f"{int(row['municipio_sede_prestador'])}",
            f"{int(row['nombre_prestador'])}",
            f"{int(row['sede_id'])}"
        ])
    
    tabla_tipos = Table(tipos_data)
    tabla_tipos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), 'lightgreen'),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'black'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 1, 'black'),
    ]))
    
    story.append(tabla_tipos)
    story.append(Spacer(1, 20))
    
    story.append(PageBreak())
    
    # ===== 5. ANÁLISIS DETALLADO DE IBAGUÉ =====
    story.append(Paragraph("5. ANÁLISIS DETALLADO DE IBAGUÉ", heading_style))
    
    if len(stats['ibague_por_tipo']) > 0:
        story.append(Image('grafico4_ibague_alto.png', width=8*inch, height=6*inch))  # Más alto
        story.append(Spacer(1, 15))
        
        # Tabla detallada de Ibagué por tipo con CAMAS/CAMILLAS
        story.append(Paragraph("5.1 Ibagué por Tipo de Capacidad (CAMAS/CAMILLAS)", subheading_style))
        ibague_data = [['Tipo de Capacidad', 'Prestadores', 'Sedes', 'Capacidad', 'Ocupada', 'Disponible', '% Ocupación']]
        
        for _, row in stats['ibague_por_tipo'].iterrows():
            estado = "🔴" if row['porcentaje_ocupacion'] >= 90 else "🟡" if row['porcentaje_ocupacion'] >= 80 else "🟢"
            ibague_data.append([
                f"{estado} {row['categoria_con_tipo']}",
                f"{int(row['nombre_prestador'])}",
                f"{int(row['sede_id'])}",
                f"{int(row['cantidad_ci_TOTAL_REPS'])}",
                f"{int(row['ocupacion_total'])}",
                f"{int(row['cantidad_ci_disponibles'])}",
                f"{row['porcentaje_ocupacion']:.1f}%"
            ])
        
        tabla_ibague = Table(ibague_data)
        tabla_ibague.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), 'lightyellow'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'black'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
        ]))
        
        story.append(tabla_ibague)
    
    story.append(Spacer(1, 20))
    
    # ===== 6. ANÁLISIS DETALLADO POR MUNICIPIO Y PRESTADOR =====
    story.append(Paragraph("6. ANÁLISIS DETALLADO: MUNICIPIOS + PRESTADORES", heading_style))
    
    # 6.1 Todos los municipios
    story.append(Paragraph("6.1 Todos los Municipios del Tolima", subheading_style))
    municipios_data = [['Municipio', 'Prestadores', 'Sedes', 'Tipos Cap.', 'Capacidad', 'Ocupada', 'Disponible', '% Ocupación']]
    
    for _, mun in stats['municipios_completo'].iterrows():
        estado = "🔴" if mun['porcentaje_ocupacion'] >= 90 else "🟡" if mun['porcentaje_ocupacion'] >= 80 else "🟢"
        municipios_data.append([
            f"{estado} {mun['municipio_sede_prestador']}",
            f"{int(mun['num_prestadores'])}",
            f"{int(mun['num_sedes'])}",
            f"{int(mun['tipos_capacidad'])}",
            f"{int(mun['cantidad_ci_TOTAL_REPS']):,}",
            f"{int(mun['ocupacion_total']):,}",
            f"{int(mun['cantidad_ci_disponibles']):,}",
            f"{mun['porcentaje_ocupacion']:.1f}%"
        ])
    
    tabla_municipios_completa = Table(municipios_data)
    tabla_municipios_completa.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), 'lightcoral'),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'black'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, 'black'),
    ]))
    
    story.append(tabla_municipios_completa)
    story.append(Spacer(1, 20))
    
    # 6.2 Prestadores principales por municipio
    story.append(Paragraph("6.2 Prestadores Principales por Municipio (Top 30)", subheading_style))
    prestadores_data = [['Municipio', 'Prestador', 'Tipo Inst.', 'Sedes', 'Tipos Cap.', 'Capacidad', 'Ocupada', '% Ocupación']]
    
    prestadores_top = stats['prestadores_detallado'].nlargest(30, 'cantidad_ci_TOTAL_REPS')
    
    for _, prest in prestadores_top.iterrows():
        estado = "🔴" if prest['porcentaje_ocupacion'] >= 90 else "🟡" if prest['porcentaje_ocupacion'] >= 80 else "🟢"
        prestadores_data.append([
            prest['municipio_sede_prestador'],
            prest['nombre_prestador'][:30] + "..." if len(prest['nombre_prestador']) > 30 else prest['nombre_prestador'],
            prest['tipo_institucion'],
            f"{int(prest['num_sedes'])}",
            f"{int(prest['tipos_capacidad'])}",
            f"{int(prest['cantidad_ci_TOTAL_REPS']):,}",
            f"{int(prest['ocupacion_total']):,}",
            f"{estado} {prest['porcentaje_ocupacion']:.1f}%"
        ])
    
    tabla_prestadores = Table(prestadores_data)
    tabla_prestadores.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), 'lightsteelblue'),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'black'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, 'black'),
    ]))
    
    story.append(tabla_prestadores)
    story.append(Spacer(1, 30))
    
    # ===== PIE DE PÁGINA =====
    story.append(Paragraph("_" * 80, styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph("INFORMACIÓN TÉCNICA", subheading_style))
    story.append(Paragraph(f"Desarrollado por: Ing. José Miguel Santos", styles['Normal']))
    story.append(Paragraph(f"Para: Secretaría de Salud del Tolima", styles['Normal']))
    story.append(Paragraph(f"© 2025 - Sistema Final Optimizado de Monitoreo Hospitalario", styles['Normal']))
    story.append(Paragraph(f"Características: CAMAS/CAMILLAS + Alertas en Tabla + Municipios + Prestadores + Gráficos Altos", styles['Normal']))
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}", styles['Normal']))
    
    # Generar PDF
    doc.build(story)
    
    # Limpiar archivos temporales
    import os
    archivos_temp = [
        'grafico1_camas_camillas_alto.png', 
        'grafico2_municipios_alto.png',
        'grafico3_tipos_camas_camillas_alto.png', 
        'grafico4_ibague_alto.png'
    ]
    for archivo in archivos_temp:
        if os.path.exists(archivo):
            os.remove(archivo)
    
    print(f"✅ PDF final optimizado generado: {archivo_salida}")

def main():
    """Función principal"""
    import sys
    
    if len(sys.argv) < 2:
        print("\n🏥 GENERADOR DE INFORMES FINAL OPTIMIZADO")
        print("=" * 85)
        print("Desarrollado por: Ing. José Miguel Santos")
        print("Para: Secretaría de Salud del Tolima")
        print("=" * 85)
        print("\nMEJORAS FINALES IMPLEMENTADAS:")
        print("📊 GRÁFICOS MÁS ALTOS: Mayor altura vertical para mejor visualización")
        print("📋 ALERTAS EN TABLA: Formato tabla para mejor estructura visual")
        print("🛏️  CAMAS/CAMILLAS: Distinción en TODOS los análisis (no solo resumen)")
        print("🏥 MUNICIPIOS + PRESTADORES: Análisis detallado por prestador específico")
        print("🎯 TABLAS OPTIMIZADAS: Mejor organización y códigos de color")
        print("📈 MAYOR DETALLE: Sedes específicas con nombres completos")
        print("\nSECCIONES OPTIMIZADAS:")
        print("✅ Resumen ejecutivo con CAMAS/CAMILLAS detallado")
        print("✅ Gráficos de gran altura para mejor visualización")
        print("✅ Alertas críticas en formato TABLA (municipios, sedes, tipos)")
        print("✅ Análisis por tipos con distinción CAMAS/CAMILLAS")
        print("✅ Ibagué detallado con CAMAS/CAMILLAS")
        print("✅ TODOS los municipios + prestadores específicos")
        print("\nUSO:")
        print("  python hospital_report_FINAL_OPTIMIZADO.py archivo.xlsx [salida.pdf]")
        return
    
    archivo_excel = sys.argv[1]
    archivo_salida = sys.argv[2] if len(sys.argv) > 2 else f"informe_final_optimizado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    try:
        print(f"\n🏥 GENERANDO INFORME FINAL OPTIMIZADO")
        print("=" * 85)
        print(f"👨‍💻 Desarrollado por: Ing. José Miguel Santos")
        print(f"🏛️  Para: Secretaría de Salud del Tolima")
        print("=" * 85)
        print(f"📂 Archivo origen: {archivo_excel}")
        print(f"📄 Archivo destino: {archivo_salida}")
        print("-" * 85)
        
        # Procesar datos con optimización final
        df = procesar_datos_final_optimizado(archivo_excel)
        
        # Calcular estadísticas optimizadas
        stats = calcular_estadisticas_optimizadas(df)
        
        # Mostrar resumen en consola
        print(f"\n📊 RESUMEN CAMAS vs CAMILLAS:")
        for _, row in stats['resumen_camas_camillas'].iterrows():
            estado = "🔴" if row['porcentaje_ocupacion'] >= 90 else "🟡" if row['porcentaje_ocupacion'] >= 80 else "🟢"
            print(f"   {estado} {row['tipo_general']}: {row['porcentaje_ocupacion']:.1f}% ocupación ({int(row['cantidad_ci_TOTAL_REPS']):,} total)")
        
        print(f"\n🗺️  RESUMEN TERRITORIAL:")
        print(f"   🌍 Tolima: {stats['tolima_general']['porcentaje']:.1f}% ocupación")
        if stats['ibague_general']:
            print(f"   🏛️  Ibagué: {stats['ibague_general']['porcentaje_ocupacion']:.1f}% ocupación")
        print(f"   📍 {len(stats['municipios_completo'])} municipios analizados")
        print(f"   🏥 {len(stats['prestadores_detallado'])} prestadores detallados")
        
        print(f"\n🚨 ALERTAS CRÍTICAS:")
        total_alertas = (len(stats['municipios_criticos']) + 
                        len(stats['tipos_criticos']) + 
                        len(stats['sedes_criticas']) +
                        len(stats['prestadores_criticos']))
        if total_alertas > 0:
            print(f"   ⚠️  {total_alertas} alertas críticas identificadas")
            if len(stats['sedes_criticas']) > 0:
                print(f"       • {len(stats['sedes_criticas'])} sedes específicas críticas")
            if len(stats['prestadores_criticos']) > 0:
                print(f"       • {len(stats['prestadores_criticos'])} prestadores críticos")
        else:
            print(f"   ✅ No hay alertas críticas")
        print()
        
        # Crear gráficos optimizados con mayor altura
        crear_graficos_optimizados_verticales(stats)
        
        # Generar PDF final optimizado
        generar_pdf_final_optimizado(stats, archivo_salida)
        
        print("=" * 85)
        print(f"🎉 ¡INFORME FINAL OPTIMIZADO GENERADO EXITOSAMENTE!")
        print(f"📄 Archivo: {archivo_salida}")
        print(f"📊 {stats['tolima_general']['capacidad']:,} camas/camillas analizadas")
        print(f"🗺️  {len(stats['municipios_completo'])} municipios completos")
        print(f"🏥 {len(stats['prestadores_detallado'])} prestadores detallados")
        print(f"🛏️  {len(stats['capacidad_con_tipo'])} tipos específicos (CAMAS/CAMILLAS)")
        print(f"📊 Gráficos optimizados con mayor altura vertical")
        print(f"📋 Alertas críticas en formato tabla mejorado")
        print("=" * 85)
        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{archivo_excel}'")
        print("   Verifica que el archivo esté en la carpeta correcta")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Revisa que el archivo Excel tenga el formato correcto")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()