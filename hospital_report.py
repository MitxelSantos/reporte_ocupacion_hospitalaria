#!/usr/bin/env python3
"""
Sistema Capacidad Hospitalaria del Tolima
Discriminado por IPS y Municipio

VERSIÓN FINAL:
- ✅ Ocupación corregida: ocupacion_ci_no_covid19
- ✅ Cambios de nombres: Hospitalización Adultos/Pediátrica
- ✅ Unificación de error: CAMAS-Intensiva Adultos → CAMAS-Cuidado Intensivo Adulto
- ✅ Subgrupos organizados con totales estéticos
- ✅ Aplicado en todas las secciones

Desarrollado por: Ing. José Miguel Santos
Para: Secretaría de Salud del Tolima
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
import warnings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame

# Para manejo de fechas del Excel
try:
    from dateutil import parser
except ImportError:
    print("⚠️ dateutil no disponible, usando datetime básico")

warnings.filterwarnings("ignore")

# Configuración global
COLORS = {
    "primary": "#722F37",  # Vinotinto tenue para Tolima
    "secondary": "#D4AF37",  # Dorado
    "success": "#4CAF50",  # Verde para NORMAL
    "warning": "#FF9800",  # Naranja para ADVERTENCIA
    "danger": "#DC143C",  # Rojo para CRÍTICO
    "white": "#FFFFFF",  # Blanco
    "light_gray": "#F5F5F5",  # Gris claro
    "header_bg": "#8B4B5C",  # Vinotinto más claro para fondo encabezado
    "subgrupo_bg": "#E8F4FD",  # Azul claro para filas de subgrupos
}

# Umbrales de ocupación
UMBRALES = {
    "critico": 90,  # ≥90% crítico
    "advertencia": 70,  # 70-89% advertencia
    "normal": 0,  # <70% normal
}

# CONFIGURACIÓN DE CATEGORIZACIÓN Y SUBGRUPOS
def definir_configuracion_categorias():
    """Definir configuración completa de categorías y subgrupos."""
    
    # 1. CAMBIOS DE NOMBRES OBLIGATORIOS
    mapeo_nombres = {
        'CAMAS-Pediátrica': 'Hospitalización Pediátrica',
        'CAMAS-Adultos': 'Hospitalización Adultos',
    }
    
    # 2. CORRECCIÓN DE ERRORES DE DIGITACIÓN (se aplica ANTES del procesamiento)
    correccion_errores = {
        'CAMAS-Intensiva Adultos': 'CAMAS-Cuidado Intensivo Adulto'
    }
    
    # 3. DEFINICIÓN DE SUBGRUPOS
    subgrupos = {
        'UCI INTENSIVO': [
            'CAMAS-Cuidado Intensivo Adulto',
            'CAMAS-Cuidado Intensivo Pediátrico'
        ],
        'UCI INTERMEDIO': [
            'CAMAS-Cuidado Intermedio Adulto', 
            'CAMAS-Cuidado Intermedio Pediátrico'
        ],
        'HOSPITALIZACIÓN': [
            'CAMAS-Pediátrica',  # Se mostrará como Hospitalización Pediátrica
            'CAMAS-Adultos'     # Se mostrará como Hospitalización Adultos
        ],
        'OBSERVACIÓN URGENCIAS': [
            'CAMILLAS-Observación Adultos Hombres',
            'CAMILLAS-Observación Adultos Mujeres',
            'CAMILLAS-Observación Pediátrica'
        ]
    }
    
    return mapeo_nombres, correccion_errores, subgrupos


class HospitalDocTemplate(BaseDocTemplate):
    """Template con encabezado institucional usando fecha de registro del Excel."""

    def __init__(self, filename, fecha_registro=None, **kwargs):
        self.allowSplitting = 1
        BaseDocTemplate.__init__(self, filename, **kwargs)

        # Fecha del registro (desde Excel) o actual como fallback
        self.fecha_registro = fecha_registro or datetime.now()

        # Header height definido como constante de clase
        self.header_height = 95  # Aumentado para evitar superposición (puntos)
        self.header_height_inches = self.header_height / 72.0  # Conversión a inches

        # Frame con márgenes consistentes
        frame = Frame(
            0.4 * inch,  # Left margin
            0.4 * inch,  # Bottom margin
            self.pagesize[0] - 0.8 * inch,  # Width (page width - left - right margins)
            self.pagesize[1]
            - (self.header_height_inches + 0.2) * inch
            - 0.4 * inch,  # Height ajustada
            id="normal",
            leftPadding=6,
            bottomPadding=6,
            rightPadding=6,
            topPadding=6,
        )

        template = PageTemplate(id="test", frames=frame, onPage=self.add_page_header)
        self.addPageTemplates([template])

    def add_page_header(self, canvas, doc):
        """Agregar encabezado institucional con fecha de registro del Excel."""
        canvas.saveState()

        page_width = doc.pagesize[0]
        page_height = doc.pagesize[1]

        # Usar height definido en __init__
        header_height = self.header_height

        # Fondo del encabezado con posición fija
        canvas.setFillColor(colors.HexColor(COLORS["header_bg"]))
        canvas.rect(0, page_height - header_height, page_width, header_height, fill=1)

        # Logo fijo - Gobernacion.png
        logo_path = "Gobernacion.png"
        if os.path.exists(logo_path):
            try:
                logo_x = 15
                logo_y = page_height - header_height + 15
                logo_size = 65

                canvas.drawImage(
                    logo_path,
                    logo_x,
                    logo_y,
                    width=logo_size,
                    height=logo_size,
                    mask="auto",
                )
            except Exception as e:
                print(f"⚠️ Error cargando logo Gobernacion.png: {e}")
        else:
            print(f"⚠️ Logo no encontrado: {logo_path}")

        # Posiciones Y fijas calculadas desde la parte superior
        canvas.setFillColor(colors.whitesmoke)

        # Texto principal - GOBERNACIÓN DEL TOLIMA
        y_titulo = page_height - 25
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(page_width / 2, y_titulo, "GOBERNACIÓN DEL TOLIMA")

        # NIT
        y_nit = page_height - 42
        canvas.setFont("Helvetica", 10)
        canvas.drawCentredString(page_width / 2, y_nit, "NIT: 800.113.672-7")

        # SECRETARIA DE SALUD
        y_secretaria = page_height - 58
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawCentredString(page_width / 2, y_secretaria, "SECRETARIA DE SALUD")

        # DIRECCION DE SEGURIDAD SOCIAL
        y_direccion = page_height - 75
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(
            page_width / 2, y_direccion, "DIRECCION DE SEGURIDAD SOCIAL"
        )

        # Información lateral con fecha de registro del Excel
        canvas.setFont("Helvetica", 8)

        # Fecha del registro (desde Excel)
        if isinstance(self.fecha_registro, str):
            fecha_str = self.fecha_registro
        else:
            fecha_str = self.fecha_registro.strftime("%d/%m/%Y %H:%M")

        y_fecha = page_height - 30
        canvas.drawRightString(page_width - 15, y_fecha, f"Fecha registro: {fecha_str}")

        # Número de página
        y_pagina = page_height - 42
        canvas.drawRightString(page_width - 15, y_pagina, f"Página {doc.page}")

        # Línea separadora en la parte inferior del encabezado
        canvas.setStrokeColor(colors.HexColor(COLORS["secondary"]))
        canvas.setLineWidth(2)
        canvas.line(
            0,
            page_height - header_height,
            page_width,
            page_height - header_height,
        )

        canvas.restoreState()


class HospitalCompletoGenerator:
    """Generador completo con subgrupos y categorización final."""

    def __init__(self):
        self.df = None
        self.fecha_procesamiento = datetime.now()
        self.todas_categorias = []
        self.mapeo_nombres, self.correccion_errores, self.subgrupos = definir_configuracion_categorias()

    def cargar_datos(self, archivo_excel):
        """Cargar los datos del Excel con correcciones y validación."""
        try:
            print(f"📂 Cargando los datos hospitalarios: {archivo_excel}")

            self.df = pd.read_excel(archivo_excel)
            print(f"📊 Datos cargados: {len(self.df)} registros")

            # Verificar columnas corregidas
            columnas_requeridas = [
                "municipio_sede_prestador",
                "nombre_prestador",
                "nombre_sede_prestador",
                "nombre_capacidad_instalada",
                "cantidad_ci_TOTAL_REPS",
                "ocupacion_ci_no_covid19",
            ]

            columnas_faltantes = [
                col for col in columnas_requeridas if col not in self.df.columns
            ]
            if columnas_faltantes:
                print(f"❌ Error: Columnas faltantes: {columnas_faltantes}")
                return False

            self._procesar_datos()
            print("✅ Datos procesados correctamente con subgrupos organizados")
            return True

        except Exception as e:
            print(f"❌ Error al cargar datos: {str(e)}")
            return False

    def _procesar_datos(self):
        """Procesar los datos con correcciones de nombres y errores."""
        print("🔄 Procesando datos hospitalarios con correcciones...")

        # Limpiar nombres de columnas
        self.df.columns = self.df.columns.str.strip()

        # 1. CORRECCIÓN DE ERRORES DE DIGITACIÓN (ANTES de todo)
        print("🔧 Aplicando correcciones de errores de digitación...")
        for error, correccion in self.correccion_errores.items():
            mask = self.df["nombre_capacidad_instalada"] == error
            if mask.any():
                count = mask.sum()
                self.df.loc[mask, "nombre_capacidad_instalada"] = correccion
                print(f"   ✅ Corregido: {error} → {correccion} ({count} registros)")

        # 2. Convertir valores numéricos
        self.df["cantidad_ci_TOTAL_REPS"] = pd.to_numeric(
            self.df["cantidad_ci_TOTAL_REPS"], errors="coerce"
        ).fillna(0)
        
        self.df["ocupacion_actual"] = pd.to_numeric(
            self.df["ocupacion_ci_no_covid19"], errors="coerce"
        ).fillna(0)

        # 3. Calcular métricas
        self.df["porcentaje_ocupacion"] = np.where(
            self.df["cantidad_ci_TOTAL_REPS"] > 0,
            (self.df["ocupacion_actual"] / self.df["cantidad_ci_TOTAL_REPS"]) * 100,
            0,
        )

        self.df["disponible"] = (
            self.df["cantidad_ci_TOTAL_REPS"] - self.df["ocupacion_actual"]
        )
        self.df["disponible"] = self.df["disponible"].clip(lower=0)

        # 4. Limpiar nombres
        self.df["municipio_sede_prestador"] = (
            self.df["municipio_sede_prestador"].str.strip().str.title()
        )
        self.df["nombre_prestador"] = self.df["nombre_prestador"].str.strip()
        self.df["nombre_capacidad_instalada"] = self.df[
            "nombre_capacidad_instalada"
        ].str.strip()

        # 5. Obtener categorías (después de correcciones)
        self.todas_categorias = sorted(self.df["nombre_capacidad_instalada"].unique())

        print(f"📊 Registros procesados: {len(self.df)}")
        print(f"🏘️ Municipios: {self.df['municipio_sede_prestador'].nunique()}")
        print(f"🏥 IPS: {self.df['nombre_prestador'].nunique()}")
        print(f"📋 Categorías encontradas: {len(self.todas_categorias)}")

        # Mostrar configuración aplicada
        print("✅ CONFIGURACIÓN APLICADA:")
        print(f"   🔧 Errores corregidos: {len(self.correccion_errores)}")
        print(f"   📝 Cambios de nombres: {len(self.mapeo_nombres)}")
        print(f"   📊 Subgrupos definidos: {len(self.subgrupos)}")

    def _extraer_fecha_registro(self):
        """Extraer fecha de registro del Excel."""
        try:
            if "fecha_registro" in self.df.columns:
                fechas = self.df["fecha_registro"].dropna()
                if not fechas.empty:
                    fecha_registro = fechas.max()

                    if isinstance(fecha_registro, str):
                        try:
                            from dateutil import parser
                            fecha_registro = parser.parse(fecha_registro)
                        except:
                            print("⚠️ No se pudo parsear fecha_registro, usando fecha actual")
                            return datetime.now()

                    print(f"✅ Fecha de registro extraída: {fecha_registro}")
                    return fecha_registro
                else:
                    print("⚠️ Columna fecha_registro vacía, usando fecha actual")
                    return datetime.now()
            else:
                print("⚠️ Columna fecha_registro no encontrada, usando fecha actual")
                return datetime.now()
        except Exception as e:
            print(f"⚠️ Error extrayendo fecha_registro: {e}, usando fecha actual")
            return datetime.now()

    def _estimar_altura_tabla(self, tabla_data, ancho_columnas=None):
        """Estimar altura aproximada de una tabla en puntos."""
        if not tabla_data:
            return 0
        
        altura_fila_header = 25
        altura_fila_normal = 15
        altura_fila_subgrupo = 18  # Filas de subgrupos ligeramente más altas
        
        num_filas = len(tabla_data)
        # Estimar que aproximadamente 20% serán filas de subgrupos
        filas_subgrupos = max(1, int(num_filas * 0.2))
        filas_normales = num_filas - filas_subgrupos - 1  # -1 por header
        
        altura_estimada = altura_fila_header + (filas_normales * altura_fila_normal) + (filas_subgrupos * altura_fila_subgrupo)
        
        return altura_estimada

    def _crear_seccion_firmas(self):
        """Crear sección de firmas institucionales."""
        estilos = getSampleStyleSheet()

        estilo_firma = ParagraphStyle(
            "EstiloFirma",
            parent=estilos["Normal"],
            fontSize=9,
            spaceAfter=4,
            spaceBefore=2,
            alignment=TA_LEFT,
            fontName="Helvetica",
        )

        estilo_firma_center = ParagraphStyle(
            "EstiloFirmaCenter",
            parent=estilos["Normal"],
            fontSize=9,
            spaceAfter=4,
            spaceBefore=2,
            alignment=TA_CENTER,
            fontName="Helvetica",
        )

        elementos_firmas = []

        elementos_firmas.append(Spacer(1, 0.4 * inch))
        elementos_firmas.append(Paragraph("Cordialmente,", estilo_firma))
        elementos_firmas.append(Spacer(1, 0.3 * inch))

        datos_firmas = [
            [
                Paragraph(
                    "<b>DOUGLAS QUINTERO TÉLLEZ</b><br/>Director de Seguridad Social<br/>Secretaria de Salud del Tolima",
                    estilo_firma_center,
                ),
                Paragraph(
                    "<b>ALISON AMAYA REYES</b><br/>Directora Desarrollo de servicios<br/>Secretaria de Salud del Tolima",
                    estilo_firma_center,
                ),
            ]
        ]

        tabla_firmas = Table(datos_firmas, colWidths=[3.5 * inch, 3.5 * inch])
        tabla_firmas.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 20),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        elementos_firmas.append(tabla_firmas)
        elementos_firmas.append(Spacer(1, 0.2 * inch))

        elementos_firmas.append(
            Paragraph(
                "<b>Proyecto:</b> Adriana Cardozo – Luis Alberto Ortiz Contratistas",
                estilo_firma,
            )
        )
        elementos_firmas.append(
            Paragraph("<b>Automatización:</b> José Miguel Santos", estilo_firma)
        )
        elementos_firmas.append(
            Paragraph(
                "<b>Reviso:</b> Aldo Eugenio Beltrán Rivera – Coordinador de Emergencias y Desastres – CRUET",
                estilo_firma,
            )
        )

        return elementos_firmas

    def _determinar_estado(self, porcentaje):
        """Determinar estado según umbral."""
        if porcentaje >= UMBRALES["critico"]:
            return "CRÍTICO"
        elif porcentaje >= UMBRALES["advertencia"]:
            return "ADVERTENCIA"
        else:
            return "NORMAL"

    def _organizar_datos_por_subgrupos(self, datos_categorias):
        """Organizar los datos por subgrupos y agregar totales."""
        datos_organizados = []
        
        # Crear un mapeo inverso de categorías a subgrupos
        categoria_a_subgrupo = {}
        for subgrupo, categorias in self.subgrupos.items():
            for categoria in categorias:
                categoria_a_subgrupo[categoria] = subgrupo
        
        # Procesar por subgrupos
        for subgrupo, categorias_subgrupo in self.subgrupos.items():
            # Agregar categorías individuales del subgrupo
            subgrupo_capacidad = 0
            subgrupo_ocupacion = 0
            categorias_encontradas = 0
            
            for categoria in categorias_subgrupo:
                if categoria in datos_categorias:
                    datos_cat = datos_categorias[categoria]
                    
                    # Aplicar cambio de nombre si existe
                    nombre_mostrar = self.mapeo_nombres.get(categoria, categoria)
                    nombre_mostrar = nombre_mostrar.replace("CAMAS-", "").replace("CAMILLAS-", "")
                    
                    # Agregar fila de categoría individual
                    datos_organizados.append({
                        'tipo': 'categoria',
                        'nombre': nombre_mostrar,
                        'capacidad': datos_cat['capacidad'],
                        'ocupacion': datos_cat['ocupacion'],
                        'disponible': datos_cat['disponible'],
                        'porcentaje': datos_cat['porcentaje'],
                        'municipios': datos_cat.get('municipios', ''),
                        'ips': datos_cat.get('ips', ''),
                        'sedes': datos_cat.get('sedes', ''),
                        'estado': datos_cat['estado']
                    })
                    
                    # Acumular para total del subgrupo
                    subgrupo_capacidad += datos_cat['capacidad']
                    subgrupo_ocupacion += datos_cat['ocupacion']
                    categorias_encontradas += 1
            
            # Agregar fila de total del subgrupo (siempre, sin importar cantidad de categorías)
            if categorias_encontradas > 0:  # CORRECCIÓN: Mostrar total siempre que haya al menos una categoría
                subgrupo_disponible = subgrupo_capacidad - subgrupo_ocupacion
                subgrupo_porcentaje = round((subgrupo_ocupacion / subgrupo_capacidad * 100), 1) if subgrupo_capacidad > 0 else 0
                subgrupo_estado = self._determinar_estado(subgrupo_porcentaje)
                
                datos_organizados.append({
                    'tipo': 'subgrupo',
                    'nombre': f"📊 TOTAL {subgrupo}",
                    'capacidad': subgrupo_capacidad,
                    'ocupacion': subgrupo_ocupacion,
                    'disponible': subgrupo_disponible,
                    'porcentaje': subgrupo_porcentaje,
                    'municipios': '',
                    'ips': '',
                    'sedes': '',
                    'estado': subgrupo_estado
                })
        
        # Agregar categorías que no pertenecen a ningún subgrupo
        for categoria, datos_cat in datos_categorias.items():
            if categoria not in categoria_a_subgrupo:
                nombre_mostrar = categoria.replace("CAMAS-", "").replace("CAMILLAS-", "")
                datos_organizados.append({
                    'tipo': 'categoria',
                    'nombre': nombre_mostrar,
                    'capacidad': datos_cat['capacidad'],
                    'ocupacion': datos_cat['ocupacion'],
                    'disponible': datos_cat['disponible'],
                    'porcentaje': datos_cat['porcentaje'],
                    'municipios': datos_cat.get('municipios', ''),
                    'ips': datos_cat.get('ips', ''),
                    'sedes': datos_cat.get('sedes', ''),
                    'estado': datos_cat['estado']
                })
        
        return datos_organizados

    def _crear_tabla_resumen_departamental(self):
        """Tabla resumen departamental con subgrupos organizados."""
        # Recopilar datos por categoría
        datos_categorias = {}
        
        for categoria in self.todas_categorias:
            df_categoria = self.df[self.df["nombre_capacidad_instalada"] == categoria]

            if len(df_categoria) > 0:
                capacidad = int(df_categoria["cantidad_ci_TOTAL_REPS"].sum())
                ocupacion = int(df_categoria["ocupacion_actual"].sum())
                disponible = capacidad - ocupacion
                porcentaje = round((ocupacion / capacidad * 100), 1) if capacidad > 0 else 0
                municipios = df_categoria["municipio_sede_prestador"].nunique()
                ips = df_categoria["nombre_prestador"].nunique()
                estado = self._determinar_estado(porcentaje)

                datos_categorias[categoria] = {
                    'capacidad': capacidad,
                    'ocupacion': ocupacion,
                    'disponible': disponible,
                    'porcentaje': porcentaje,
                    'municipios': municipios,
                    'ips': ips,
                    'estado': estado
                }

        # Organizar por subgrupos
        datos_organizados = self._organizar_datos_por_subgrupos(datos_categorias)
        
        # Convertir a formato de tabla
        datos_tabla = []
        for item in datos_organizados:
            datos_tabla.append([
                item['nombre'],
                f"{item['capacidad']:,}",
                f"{item['ocupacion']:,}",
                f"{item['disponible']:,}",
                f"{item['porcentaje']}%",
                str(item['municipios']),
                str(item['ips']),
                item['estado'],
                item['tipo']  # Para identificar el tipo de fila
            ])

        # Totales generales
        total_capacidad = int(self.df["cantidad_ci_TOTAL_REPS"].sum())
        total_ocupacion = int(self.df["ocupacion_actual"].sum())
        total_disponible = total_capacidad - total_ocupacion
        total_porcentaje = round((total_ocupacion / total_capacidad * 100), 1) if total_capacidad > 0 else 0
        total_municipios = self.df["municipio_sede_prestador"].nunique()
        total_ips = self.df["nombre_prestador"].nunique()
        estado_general = self._determinar_estado(total_porcentaje)

        datos_tabla.append([
            "TOTAL DEPARTAMENTO",
            f"{total_capacidad:,}",
            f"{total_ocupacion:,}",
            f"{total_disponible:,}",
            f"{total_porcentaje}%",
            str(total_municipios),
            str(total_ips),
            estado_general,
            "total"
        ])

        headers = [
            "Tipo de Servicio",
            "Capacidad\nInstalada", 
            "Ocupación\nActual",
            "Disponible",
            "% Ocupación",
            "Municipios",
            "IPS",
            "Estado",
            "tipo_fila"  # Columna oculta para identificar tipo
        ]

        return [headers] + datos_tabla

    def _crear_tabla_ips_por_municipio(self, municipio):
        """Crear tabla IPS por municipio con subgrupos organizados."""
        df_municipio = self.df[self.df["municipio_sede_prestador"] == municipio]

        if df_municipio.empty:
            return None

        datos_tabla = []

        # Agrupar por IPS
        for ips in df_municipio["nombre_prestador"].unique():
            df_ips = df_municipio[df_municipio["nombre_prestador"] == ips]

            # Totales por IPS
            total_cap_ips = int(df_ips["cantidad_ci_TOTAL_REPS"].sum())
            total_ocup_ips = int(df_ips["ocupacion_actual"].sum())
            total_disp_ips = total_cap_ips - total_ocup_ips
            total_porc_ips = round((total_ocup_ips / total_cap_ips * 100), 1) if total_cap_ips > 0 else 0
            estado_ips = self._determinar_estado(total_porc_ips)

            # Fila resumen IPS
            nombre_ips_corto = ips[:50] + "..." if len(ips) > 50 else ips
            datos_tabla.append([
                f"🏥 {nombre_ips_corto}",
                f"{total_cap_ips:,}",
                f"{total_ocup_ips:,}",
                f"{total_disp_ips:,}",
                f"{total_porc_ips}%",
                estado_ips,
                "ips"
            ])

            # Recopilar categorías de esta IPS y organizarlas por subgrupos
            datos_categorias_ips = {}
            categorias_ips = df_ips["nombre_capacidad_instalada"].unique()
            
            for categoria in sorted(categorias_ips):
                df_cat_ips = df_ips[df_ips["nombre_capacidad_instalada"] == categoria]

                if len(df_cat_ips) > 0:
                    cap = int(df_cat_ips["cantidad_ci_TOTAL_REPS"].sum())
                    ocup = int(df_cat_ips["ocupacion_actual"].sum())
                    disp = cap - ocup
                    porc = round((ocup / cap * 100), 1) if cap > 0 else 0
                    estado_cat = self._determinar_estado(porc)

                    datos_categorias_ips[categoria] = {
                        'capacidad': cap,
                        'ocupacion': ocup,
                        'disponible': disp,
                        'porcentaje': porc,
                        'estado': estado_cat
                    }

            # Organizar por subgrupos para esta IPS
            datos_organizados_ips = self._organizar_datos_por_subgrupos(datos_categorias_ips)
            
            # Agregar filas organizadas por subgrupos
            for item in datos_organizados_ips:
                prefijo = "   📊 " if item['tipo'] == 'subgrupo' else "   └─ "
                datos_tabla.append([
                    f"{prefijo}{item['nombre']}",
                    f"{item['capacidad']:,}",
                    f"{item['ocupacion']:,}",
                    f"{item['disponible']:,}",
                    f"{item['porcentaje']}%",
                    item['estado'],
                    item['tipo']
                ])

        # Total del municipio
        total_cap_mun = int(df_municipio["cantidad_ci_TOTAL_REPS"].sum())
        total_ocup_mun = int(df_municipio["ocupacion_actual"].sum())
        total_disp_mun = total_cap_mun - total_ocup_mun
        total_porc_mun = round((total_ocup_mun / total_cap_mun * 100), 1) if total_cap_mun > 0 else 0
        estado_mun = self._determinar_estado(total_porc_mun)

        datos_tabla.append([
            f"📊 TOTAL {municipio.upper()}",
            f"{total_cap_mun:,}",
            f"{total_ocup_mun:,}",
            f"{total_disp_mun:,}",
            f"{total_porc_mun}%",
            estado_mun,
            "total"
        ])

        headers = [
            "IPS / Tipo de Servicio",
            "Capacidad\nInstalada",
            "Ocupación\nActual", 
            "Disponible",
            "% Ocupación",
            "Estado",
            "tipo_fila"
        ]

        return [headers] + datos_tabla

    def _crear_tabla_federico_lleras_final(self):
        """Crear tabla Federico Lleras con subgrupos organizados."""
        df_federico = self.df[
            self.df["nombre_prestador"].str.contains(
                "FEDERICO LLERAS ACOSTA", case=False, na=False
            )
        ]

        if df_federico.empty:
            return None

        # Recopilar datos por categoría
        datos_categorias = {}
        categorias_federico = df_federico["nombre_capacidad_instalada"].unique()
        
        for categoria in sorted(categorias_federico):
            df_cat = df_federico[df_federico["nombre_capacidad_instalada"] == categoria]

            if len(df_cat) > 0:
                capacidad = int(df_cat["cantidad_ci_TOTAL_REPS"].sum())
                ocupacion = int(df_cat["ocupacion_actual"].sum())
                disponible = capacidad - ocupacion
                porcentaje = round((ocupacion / capacidad * 100), 1) if capacidad > 0 else 0
                sedes = df_cat["nombre_sede_prestador"].nunique()
                estado = self._determinar_estado(porcentaje)

                datos_categorias[categoria] = {
                    'capacidad': capacidad,
                    'ocupacion': ocupacion,
                    'disponible': disponible,
                    'porcentaje': porcentaje,
                    'sedes': sedes,
                    'estado': estado
                }

        # Organizar por subgrupos
        datos_organizados = self._organizar_datos_por_subgrupos(datos_categorias)
        
        # Convertir a formato de tabla
        datos_tabla = []
        for item in datos_organizados:
            datos_tabla.append([
                item['nombre'],
                f"{item['capacidad']:,}",
                f"{item['ocupacion']:,}",
                f"{item['disponible']:,}",
                f"{item['porcentaje']}%",
                str(item['sedes']),
                item['estado'],
                item['tipo']
            ])

        # Total Federico Lleras
        total_capacidad = int(df_federico["cantidad_ci_TOTAL_REPS"].sum())
        total_ocupacion = int(df_federico["ocupacion_actual"].sum())
        total_disponible = total_capacidad - total_ocupacion
        total_porcentaje = round((total_ocupacion / total_capacidad * 100), 1) if total_capacidad > 0 else 0
        total_sedes = df_federico["nombre_sede_prestador"].nunique()
        estado_general = self._determinar_estado(total_porcentaje)

        datos_tabla.append([
            "TOTAL FEDERICO LLERAS",
            f"{total_capacidad:,}",
            f"{total_ocupacion:,}",
            f"{total_disponible:,}",
            f"{total_porcentaje}%",
            str(total_sedes),
            estado_general,
            "total"
        ])

        headers = [
            "Tipo de Servicio",
            "Capacidad\nInstalada",
            "Ocupación\nActual",
            "Disponible", 
            "% Ocupación",
            "Sedes",
            "Estado",
            "tipo_fila"
        ]

        return [headers] + datos_tabla

    def _crear_estilo_tabla_con_colores_y_subgrupos(self):
        """Crear estilo de tabla con colores diferenciados para subgrupos."""
        return TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLORS["primary"])),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),  # Nombres alineados a la izquierda
            ]
        )

    def _aplicar_colores_estado_y_subgrupos(self, tabla_style, tabla_data, col_estado_index):
        """Aplicar colores diferenciados para estados y subgrupos."""
        col_tipo_index = len(tabla_data[0]) - 1  # Última columna es tipo_fila
        
        for i, fila in enumerate(tabla_data[1:], 1):  # Saltar encabezado
            if len(fila) > col_estado_index:
                estado = fila[col_estado_index]
                tipo_fila = fila[col_tipo_index] if len(fila) > col_tipo_index else 'categoria'
                
                # Colores para filas de subgrupos
                if tipo_fila == 'subgrupo':
                    tabla_style.add(
                        "BACKGROUND",
                        (0, i),
                        (-2, i),  # Todas las columnas excepto la última (tipo_fila)
                        colors.HexColor(COLORS["subgrupo_bg"])
                    )
                    tabla_style.add(
                        "FONTNAME",
                        (0, i),
                        (-2, i),
                        "Helvetica-Bold"
                    )
                
                # Colores para filas de totales
                elif tipo_fila == 'total':
                    tabla_style.add(
                        "BACKGROUND",
                        (0, i),
                        (-2, i),
                        colors.HexColor("#E3F2FD")
                    )
                    tabla_style.add(
                        "FONTNAME",
                        (0, i),
                        (-2, i),
                        "Helvetica-Bold"
                    )
                
                # Colores por estado (en la columna de estado)
                if "CRÍTICO" in estado:
                    tabla_style.add(
                        "BACKGROUND",
                        (col_estado_index, i),
                        (col_estado_index, i),
                        colors.HexColor("#FFCDD2"),
                    )
                    tabla_style.add(
                        "TEXTCOLOR",
                        (col_estado_index, i),
                        (col_estado_index, i),
                        colors.HexColor("#B71C1C"),
                    )
                elif "ADVERTENCIA" in estado:
                    tabla_style.add(
                        "BACKGROUND",
                        (col_estado_index, i),
                        (col_estado_index, i),
                        colors.HexColor("#FFF3E0"),
                    )
                    tabla_style.add(
                        "TEXTCOLOR",
                        (col_estado_index, i),
                        (col_estado_index, i),
                        colors.HexColor("#E65100"),
                    )
                else:  # NORMAL
                    tabla_style.add(
                        "BACKGROUND",
                        (col_estado_index, i),
                        (col_estado_index, i),
                        colors.HexColor("#E8F5E8"),
                    )
                    tabla_style.add(
                        "TEXTCOLOR",
                        (col_estado_index, i),
                        (col_estado_index, i),
                        colors.HexColor("#2E7D32"),
                    )

    def generar_informe_completo(self, archivo_salida=None):
        """Generar informe completo con subgrupos organizados."""
        if archivo_salida is None:
            timestamp = self.fecha_procesamiento.strftime("%Y%m%d_%H%M%S")
            archivo_salida = f"informe_hospitalario_completo_{timestamp}.pdf"

        print(f"📄 Generando informe hospitalario completo con subgrupos: {archivo_salida}")

        # Extraer fecha de registro del Excel
        fecha_registro = self._extraer_fecha_registro()

        # Márgenes ajustados
        header_height_inches = 95 / 72.0

        doc = HospitalDocTemplate(
            archivo_salida,
            fecha_registro=fecha_registro,
            pagesize=A4,
            rightMargin=0.4 * inch,
            leftMargin=0.4 * inch,
            topMargin=(header_height_inches + 0.25) * inch,
            bottomMargin=0.4 * inch,
        )

        elementos = []

        # Estilos
        estilos = getSampleStyleSheet()

        titulo_principal = ParagraphStyle(
            "TituloPrincipal",
            parent=estilos["Title"],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor(COLORS["primary"]),
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        titulo_seccion = ParagraphStyle(
            "TituloSeccion",
            parent=estilos["Heading1"],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=6,
            textColor=colors.HexColor(COLORS["primary"]),
            fontName="Helvetica-Bold",
        )

        texto_normal = ParagraphStyle(
            "TextoNormal",
            parent=estilos["Normal"],
            fontSize=9,
            spaceAfter=8,
            spaceBefore=4,
            alignment=TA_JUSTIFY,
        )

        texto_small = ParagraphStyle(
            "TextoSmall",
            parent=estilos["Normal"],
            fontSize=8,
            spaceAfter=6,
            spaceBefore=3,
            alignment=TA_JUSTIFY,
        )

        # ======================================================================
        # PORTADA OPTIMIZADA
        # ======================================================================
        elementos.append(Spacer(1, 0.3 * inch))
        elementos.append(
            Paragraph("INFORME DE CAPACIDAD HOSPITALARIA", titulo_principal)
        )

        # EXPLICACIÓN DE UMBRALES
        elementos.append(Spacer(1, 0.2 * inch))
        elementos.append(Paragraph("UMBRALES DE ESTADO DE OCUPACIÓN", titulo_seccion))

        explicacion_umbrales = f"""
        • <b>🟢 NORMAL:</b> Menos del {UMBRALES['advertencia']}% de ocupación<br/>
        • <b>🟡 ADVERTENCIA:</b> Entre {UMBRALES['advertencia']}% y {UMBRALES['critico']-1}% de ocupación<br/>
        • <b>🔴 CRÍTICO:</b> {UMBRALES['critico']}% o más de ocupación<br/>
        """

        elementos.append(Paragraph(explicacion_umbrales, texto_normal))

        # ======================================================================
        # RESUMEN DEPARTAMENTAL CON SUBGRUPOS
        # ======================================================================
        elementos.append(Spacer(1, 0.3 * inch))
        elementos.append(
            Paragraph("1. RESUMEN DEPARTAMENTO DEL TOLIMA", titulo_seccion)
        )

        tabla_departamental = self._crear_tabla_resumen_departamental()
        if tabla_departamental:
            tabla_style = self._crear_estilo_tabla_con_colores_y_subgrupos()
            self._aplicar_colores_estado_y_subgrupos(tabla_style, tabla_departamental, 7)

            # Remover la columna tipo_fila (última columna) para mostrar
            tabla_display = []
            for fila in tabla_departamental:
                tabla_display.append(fila[:-1])  # Excluir última columna

            tabla_pdf = Table(tabla_display, repeatRows=1)
            tabla_pdf.setStyle(tabla_style)
            elementos.append(KeepTogether([tabla_pdf]))

        # ======================================================================
        # IBAGUÉ CON SUBGRUPOS
        # ======================================================================
        elementos.append(Spacer(1, 0.3 * inch))
        
        tabla_ibague = self._crear_tabla_ips_por_municipio("Ibagué")
        if tabla_ibague:
            titulo_ibague = Paragraph("2. IBAGUÉ", titulo_seccion)
            
            tabla_style = self._crear_estilo_tabla_con_colores_y_subgrupos()
            self._aplicar_colores_estado_y_subgrupos(tabla_style, tabla_ibague, 5)

            # Remover columna tipo_fila
            tabla_display = []
            for fila in tabla_ibague:
                tabla_display.append(fila[:-1])

            tabla_pdf = Table(tabla_display, repeatRows=1)
            tabla_pdf.setStyle(tabla_style)
            
            elementos.append(KeepTogether([
                titulo_ibague,
                Spacer(1, 0.05 * inch),
                tabla_pdf
            ]))
        else:
            elementos.append(Paragraph("2. IBAGUÉ", titulo_seccion))
            elementos.append(
                Paragraph("⚠️ No se encontraron datos para Ibagué", texto_normal)
            )

        elementos.append(PageBreak())

        # ======================================================================
        # OTROS MUNICIPIOS CON SUBGRUPOS
        # ======================================================================
        elementos.append(Spacer(1, 0.1 * inch))
        elementos.append(Paragraph("3. OTROS MUNICIPIOS DEL TOLIMA", titulo_seccion))

        otros_municipios = [
            m for m in self.df["municipio_sede_prestador"].unique() if m != "Ibagué"
        ]
        otros_municipios.sort()

        print(f"📋 Procesando {len(otros_municipios)} municipios con subgrupos...")

        municipios_en_pagina_actual = 0
        espacio_usado_actual = 0
        espacio_disponible_por_pagina = 550

        for i, municipio in enumerate(otros_municipios):
            tabla_municipio = self._crear_tabla_ips_por_municipio(municipio)
            
            if tabla_municipio:
                titulo_municipio = Paragraph(f"3.{i+1}. {municipio.upper()}", titulo_seccion)
                
                altura_estimada = self._estimar_altura_tabla(tabla_municipio)
                altura_con_titulo = altura_estimada + 40

                if espacio_usado_actual + altura_con_titulo > espacio_disponible_por_pagina and municipios_en_pagina_actual > 0:
                    elementos.append(PageBreak())
                    elementos.append(Spacer(1, 0.1 * inch))
                    municipios_en_pagina_actual = 0
                    espacio_usado_actual = 0

                tabla_style = self._crear_estilo_tabla_con_colores_y_subgrupos()
                self._aplicar_colores_estado_y_subgrupos(tabla_style, tabla_municipio, 5)

                # Remover columna tipo_fila
                tabla_display = []
                for fila in tabla_municipio:
                    tabla_display.append(fila[:-1])

                tabla_pdf = Table(tabla_display, repeatRows=1)
                tabla_pdf.setStyle(tabla_style)
                
                elementos.append(KeepTogether([
                    titulo_municipio,
                    Spacer(1, 0.05 * inch),
                    tabla_pdf,
                    Spacer(1, 0.05 * inch)
                ]))

                municipios_en_pagina_actual += 1
                espacio_usado_actual += altura_con_titulo + 5

            else:
                titulo_municipio = Paragraph(f"3.{i+1}. {municipio.upper()}", titulo_seccion)
                mensaje_sin_datos = Paragraph(
                    f"⚠️ No se encontraron datos para {municipio}", texto_small
                )
                
                elementos.append(KeepTogether([
                    titulo_municipio,
                    Spacer(1, 0.02 * inch),
                    mensaje_sin_datos,
                    Spacer(1, 0.05 * inch)
                ]))
                
                municipios_en_pagina_actual += 1
                espacio_usado_actual += 35

        elementos.append(PageBreak())

        # ======================================================================
        # HOSPITAL FEDERICO LLERAS CON SUBGRUPOS
        # ======================================================================
        elementos.append(Spacer(1, 0.1 * inch))
        
        tabla_federico = self._crear_tabla_federico_lleras_final()
        if tabla_federico:
            titulo_federico = Paragraph("4. HOSPITAL FEDERICO LLERAS ACOSTA", titulo_seccion)
            
            tabla_style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLORS["danger"])),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ]
            )

            self._aplicar_colores_estado_y_subgrupos(tabla_style, tabla_federico, 6)

            # Remover columna tipo_fila
            tabla_display = []
            for fila in tabla_federico:
                tabla_display.append(fila[:-1])

            tabla_pdf = Table(tabla_display, repeatRows=1)
            tabla_pdf.setStyle(tabla_style)
            
            elementos.append(KeepTogether([
                titulo_federico,
                Spacer(1, 0.1 * inch),
                tabla_pdf
            ]))
        else:
            elementos.append(Paragraph("4. HOSPITAL FEDERICO LLERAS ACOSTA", titulo_seccion))
            elementos.append(
                Paragraph(
                    "⚠️ <b>Hospital Federico Lleras Acosta no encontrado</b>",
                    texto_normal,
                )
            )

        # ======================================================================
        # SECCIÓN DE FIRMAS
        # ======================================================================
        elementos.extend(self._crear_seccion_firmas())

        # Construir documento
        try:
            doc.build(elementos)
            print(f"✅ Informe hospitalario completo generado: {archivo_salida}")
            print(f"📅 Fecha de registro utilizada: {fecha_registro}")
            print(f"🎯 CARACTERÍSTICAS FINALES:")
            print(f"   ✅ Ocupación corregida: ocupacion_ci_no_covid19")
            print(f"   ✅ Cambios de nombres aplicados")
            print(f"   ✅ Errores de digitación corregidos")
            print(f"   ✅ Subgrupos organizados con totales estéticos")
            print(f"   ✅ Aplicado en todas las secciones")
            return archivo_salida
        except Exception as e:
            print(f"❌ Error generando PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """Función principal."""
    print("🏥" + "=" * 70)
    print("=" * 72)
    print("   Desarrollado por: Ing. José Miguel Santos")
    print("   Para: Secretaría de Salud del Tolima")
    print("   VERSIÓN FINAL: Subgrupos Organizados + Totales Estéticos")
    print("=" * 72)

    if len(sys.argv) < 2:
        print("📋 USO DEL PROGRAMA:")
        print("   python hospital_report.py <archivo_excel>")
        print("")
        print("📊 EJEMPLO:")
        print("   python hospital_report.py Detalle_Ocupacion_CI.xlsx")
        print("")
        print("🎯 CARACTERÍSTICAS FINALES:")
        print("   ✅ Ocupación real: ocupacion_ci_no_covid19")
        print("   ✅ Hospitalización Adultos/Pediátrica")
        print("   ✅ Errores de digitación corregidos")
        print("   ✅ Subgrupos: UCI Intensivo, UCI Intermedio, Hospitalización, Urgencias")
        print("   ✅ Totales estéticos por subgrupo")
        print("   ✅ Aplicado en todas las secciones")
        return

    archivo_excel = sys.argv[1]

    if not os.path.exists(archivo_excel):
        print(f"❌ Error: El archivo '{archivo_excel}' no existe.")
        return

    generador = HospitalCompletoGenerator()

    try:
        if not generador.cargar_datos(archivo_excel):
            print("❌ Error al cargar los datos.")
            return

        archivo_generado = generador.generar_informe_completo()

        if archivo_generado:
            print("🎉" + "=" * 70)
            print("✅ INFORME HOSPITALARIO FINAL GENERADO EXITOSAMENTE")
            print(f"📄 Archivo: {archivo_generado}")
            print(f"📊 Registros procesados: {len(generador.df):,}")

            # Estadísticas finales
            total_capacidad = generador.df["cantidad_ci_TOTAL_REPS"].sum()
            total_ocupacion = generador.df["ocupacion_actual"].sum()
            porcentaje_general = (
                round((total_ocupacion / total_capacidad * 100), 1)
                if total_capacidad > 0
                else 0
            )

            print(f"   🏘️ Municipios incluidos: {generador.df['municipio_sede_prestador'].nunique()}")
            print(f"   🏥 IPS analizadas: {generador.df['nombre_prestador'].nunique()}")
            print(f"   📋 Categorías procesadas: {len(generador.todas_categorias)}")
            print(f"   🎯 Capacidad total: {total_capacidad:,} unidades")
            print(f"   📈 Ocupación REAL: {total_ocupacion:,} pacientes ({porcentaje_general}%)")

            print("=" * 72)
            print("🎯 VERSIÓN FINAL COMPLETA:")
            print("   ✅ Ocupación corregida con datos reales")
            print("   ✅ Cambios de nombres aplicados")
            print("   ✅ Errores de digitación unificados")
            print("   ✅ Subgrupos organizados estéticamente")
            print("   ✅ Totales por subgrupo en todas las secciones")
            print("   ✅ Títulos y tablas siempre juntos")
            print("   ✅ Optimización de espacios")
            print("   ✅ Sistema completamente funcional")
            print("=" * 72)
        else:
            print("❌ Error al generar el informe.")

    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()