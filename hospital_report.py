#!/usr/bin/env python3
"""
Sistema Capacidad Hospitalaria del Tolima
Discriminado por IPS y Municipio

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
}

# Umbrales de ocupación
UMBRALES = {
    "critico": 90,  # ≥90% crítico
    "advertencia": 70,  # 70-89% advertencia
    "normal": 0,  # <70% normal
}


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
    """Generador completo con las categorías del Excel."""

    def __init__(self):
        self.df = None
        self.fecha_procesamiento = datetime.now()
        self.todas_categorias = []

    def cargar_datos(self, archivo_excel):
        """Cargar los datos del Excel."""
        try:
            print(f"📂 Cargando los datos hospitalarios: {archivo_excel}")

            self.df = pd.read_excel(archivo_excel)
            print(f"📊 Datos cargados: {len(self.df)} registros")

            # Verificar columnas esenciales
            columnas_requeridas = [
                "municipio_sede_prestador",
                "nombre_prestador",
                "nombre_sede_prestador",
                "nombre_capacidad_instalada",
                "cantidad_ci_TOTAL_REPS",
                "total_ingresos_paciente_servicio",
            ]

            columnas_faltantes = [
                col for col in columnas_requeridas if col not in self.df.columns
            ]
            if columnas_faltantes:
                print(f"❌ Error: Columnas faltantes: {columnas_faltantes}")
                return False

            self._procesar_datos()
            print("✅ Datos procesados correctamente")
            return True

        except Exception as e:
            print(f"❌ Error al cargar datos: {str(e)}")
            return False

    def _procesar_datos(self):
        """Procesar los datos."""
        print("🔄 Procesando datos hospitalarios...")

        # Limpiar nombres de columnas
        self.df.columns = self.df.columns.str.strip()

        # Convertir valores numéricos
        self.df["cantidad_ci_TOTAL_REPS"] = pd.to_numeric(
            self.df["cantidad_ci_TOTAL_REPS"], errors="coerce"
        ).fillna(0)
        self.df["total_ingresos_paciente_servicio"] = pd.to_numeric(
            self.df["total_ingresos_paciente_servicio"], errors="coerce"
        ).fillna(0)

        # Calcular porcentaje de ocupación
        self.df["porcentaje_ocupacion"] = np.where(
            self.df["cantidad_ci_TOTAL_REPS"] > 0,
            (
                self.df["total_ingresos_paciente_servicio"]
                / self.df["cantidad_ci_TOTAL_REPS"]
            )
            * 100,
            0,
        )

        # Calcular disponible
        self.df["disponible"] = (
            self.df["cantidad_ci_TOTAL_REPS"]
            - self.df["total_ingresos_paciente_servicio"]
        )
        self.df["disponible"] = self.df["disponible"].clip(lower=0)

        # Limpiar nombres
        self.df["municipio_sede_prestador"] = (
            self.df["municipio_sede_prestador"].str.strip().str.title()
        )
        self.df["nombre_prestador"] = self.df["nombre_prestador"].str.strip()
        self.df["nombre_capacidad_instalada"] = self.df[
            "nombre_capacidad_instalada"
        ].str.strip()

        # Obtener TODAS las categorías del Excel
        self.todas_categorias = sorted(self.df["nombre_capacidad_instalada"].unique())

        print(f"📊 Registros procesados: {len(self.df)}")
        print(f"🏘️ Municipios: {self.df['municipio_sede_prestador'].nunique()}")
        print(f"🏥 IPS: {self.df['nombre_prestador'].nunique()}")
        print(f"📋 Categorías encontradas: {len(self.todas_categorias)}")

        # Mostrar todas las categorías
        print("📋 CATEGORÍAS DEL EXCEL:")
        for i, categoria in enumerate(self.todas_categorias, 1):
            count = len(self.df[self.df["nombre_capacidad_instalada"] == categoria])
            print(f"   {i:2d}. {categoria} ({count} registros)")

    def _extraer_fecha_registro(self):
        """Extraer fecha de registro del Excel."""
        try:
            if "fecha_registro" in self.df.columns:
                # Obtener la fecha más reciente (o común) del Excel
                fechas = self.df["fecha_registro"].dropna()
                if not fechas.empty:
                    # Usar la fecha más reciente
                    fecha_registro = fechas.max()

                    # Convertir a datetime si es string
                    if isinstance(fecha_registro, str):
                        try:
                            from dateutil import parser

                            fecha_registro = parser.parse(fecha_registro)
                        except:
                            # Si no se puede parsear, usar fecha actual
                            print(
                                "⚠️ No se pudo parsear fecha_registro, usando fecha actual"
                            )
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

    def _crear_seccion_firmas(self):
        """Crear sección de firmas institucionales."""
        estilos = getSampleStyleSheet()

        # Estilo para firmas
        estilo_firma = ParagraphStyle(
            "EstiloFirma",
            parent=estilos["Normal"],
            fontSize=9,
            spaceAfter=4,
            spaceBefore=2,
            alignment=TA_LEFT,
            fontName="Helvetica",
        )

        estilo_firma_bold = ParagraphStyle(
            "EstiloFirmaBold",
            parent=estilos["Normal"],
            fontSize=9,
            spaceAfter=4,
            spaceBefore=2,
            alignment=TA_LEFT,
            fontName="Helvetica-Bold",
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

        # Separador antes de firmas
        elementos_firmas.append(Spacer(1, 0.4 * inch))
        elementos_firmas.append(Paragraph("Cordialmente,", estilo_firma))
        elementos_firmas.append(Spacer(1, 0.3 * inch))

        # Crear tabla de firmas principales (2 columnas)
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

        # Información adicional del equipo
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

    def _crear_tabla_resumen_departamental(self):
        """Tabla resumen con las categorías del departamento."""
        datos_tabla = []

        for categoria in self.todas_categorias:
            df_categoria = self.df[self.df["nombre_capacidad_instalada"] == categoria]

            if len(df_categoria) > 0:
                capacidad = int(df_categoria["cantidad_ci_TOTAL_REPS"].sum())
                ocupacion = int(df_categoria["total_ingresos_paciente_servicio"].sum())
                disponible = capacidad - ocupacion
                porcentaje = (
                    round((ocupacion / capacidad * 100), 1) if capacidad > 0 else 0
                )
                municipios = df_categoria["municipio_sede_prestador"].nunique()
                ips = df_categoria["nombre_prestador"].nunique()

                estado = self._determinar_estado(porcentaje)

                datos_tabla.append(
                    [
                        categoria,
                        f"{capacidad:,}",
                        f"{ocupacion:,}",
                        f"{disponible:,}",
                        f"{porcentaje}%",
                        str(municipios),
                        str(ips),
                        estado,
                    ]
                )

        # Totales generales
        total_capacidad = int(self.df["cantidad_ci_TOTAL_REPS"].sum())
        total_ocupacion = int(self.df["total_ingresos_paciente_servicio"].sum())
        total_disponible = total_capacidad - total_ocupacion
        total_porcentaje = (
            round((total_ocupacion / total_capacidad * 100), 1)
            if total_capacidad > 0
            else 0
        )
        total_municipios = self.df["municipio_sede_prestador"].nunique()
        total_ips = self.df["nombre_prestador"].nunique()

        estado_general = self._determinar_estado(total_porcentaje)

        datos_tabla.append(
            [
                "TOTAL DEPARTAMENTO",
                f"{total_capacidad:,}",
                f"{total_ocupacion:,}",
                f"{total_disponible:,}",
                f"{total_porcentaje}%",
                str(total_municipios),
                str(total_ips),
                estado_general,
            ]
        )

        headers = [
            "Tipo de Servicio",
            "Capacidad\nInstalada",
            "Ocupación\nActual",
            "Disponible",
            "% Ocupación",
            "Municipios",
            "IPS",
            "Estado",
        ]

        return [headers] + datos_tabla

    def _crear_tabla_ips_por_municipio(self, municipio):
        """Crear tabla IPS específica por municipio."""
        df_municipio = self.df[self.df["municipio_sede_prestador"] == municipio]

        if df_municipio.empty:
            return None

        datos_tabla = []

        # Agrupar por IPS
        for ips in df_municipio["nombre_prestador"].unique():
            df_ips = df_municipio[df_municipio["nombre_prestador"] == ips]

            # Totales por IPS
            total_cap_ips = int(df_ips["cantidad_ci_TOTAL_REPS"].sum())
            total_ocup_ips = int(df_ips["total_ingresos_paciente_servicio"].sum())
            total_disp_ips = total_cap_ips - total_ocup_ips
            total_porc_ips = (
                round((total_ocup_ips / total_cap_ips * 100), 1)
                if total_cap_ips > 0
                else 0
            )

            estado_ips = self._determinar_estado(total_porc_ips)

            # Fila resumen IPS
            nombre_ips_corto = ips[:50] + "..." if len(ips) > 50 else ips
            datos_tabla.append(
                [
                    f"🏥 {nombre_ips_corto}",
                    f"{total_cap_ips:,}",
                    f"{total_ocup_ips:,}",
                    f"{total_disp_ips:,}",
                    f"{total_porc_ips}%",
                    estado_ips,
                ]
            )

            # Detalles por categoría de esta IPS (solo las que tiene)
            categorias_ips = df_ips["nombre_capacidad_instalada"].unique()
            for categoria in sorted(categorias_ips):
                df_cat_ips = df_ips[df_ips["nombre_capacidad_instalada"] == categoria]

                if len(df_cat_ips) > 0:
                    cap = int(df_cat_ips["cantidad_ci_TOTAL_REPS"].sum())
                    ocup = int(df_cat_ips["total_ingresos_paciente_servicio"].sum())
                    disp = cap - ocup
                    porc = round((ocup / cap * 100), 1) if cap > 0 else 0

                    estado_cat = self._determinar_estado(porc)

                    # Nombre de categoría más corto
                    cat_corto = categoria.replace("CAMAS-", "").replace("CAMILLAS-", "")

                    datos_tabla.append(
                        [
                            f"   └─ {cat_corto}",
                            f"{cap:,}",
                            f"{ocup:,}",
                            f"{disp:,}",
                            f"{porc}%",
                            estado_cat,
                        ]
                    )

        # Total del municipio
        total_cap_mun = int(df_municipio["cantidad_ci_TOTAL_REPS"].sum())
        total_ocup_mun = int(df_municipio["total_ingresos_paciente_servicio"].sum())
        total_disp_mun = total_cap_mun - total_ocup_mun
        total_porc_mun = (
            round((total_ocup_mun / total_cap_mun * 100), 1) if total_cap_mun > 0 else 0
        )

        estado_mun = self._determinar_estado(total_porc_mun)

        datos_tabla.append(
            [
                f"📊 TOTAL {municipio.upper()}",
                f"{total_cap_mun:,}",
                f"{total_ocup_mun:,}",
                f"{total_disp_mun:,}",
                f"{total_porc_mun}%",
                estado_mun,
            ]
        )

        headers = [
            "IPS / Tipo de Servicio",
            "Capacidad\nInstalada",
            "Ocupación\nActual",
            "Disponible",
            "% Ocupación",
            "Estado",
        ]

        return [headers] + datos_tabla

    def _crear_tabla_federico_lleras_final(self):
        """Crear tabla final específica del Hospital Federico Lleras."""
        df_federico = self.df[
            self.df["nombre_prestador"].str.contains(
                "FEDERICO LLERAS ACOSTA", case=False, na=False
            )
        ]

        if df_federico.empty:
            return None

        datos_tabla = []

        # Por cada categoría que tiene el Federico Lleras
        categorias_federico = df_federico["nombre_capacidad_instalada"].unique()
        for categoria in sorted(categorias_federico):
            df_cat = df_federico[df_federico["nombre_capacidad_instalada"] == categoria]

            if len(df_cat) > 0:
                capacidad = int(df_cat["cantidad_ci_TOTAL_REPS"].sum())
                ocupacion = int(df_cat["total_ingresos_paciente_servicio"].sum())
                disponible = capacidad - ocupacion
                porcentaje = (
                    round((ocupacion / capacidad * 100), 1) if capacidad > 0 else 0
                )
                sedes = df_cat["nombre_sede_prestador"].nunique()

                estado = self._determinar_estado(porcentaje)

                # Nombre más corto para la tabla
                cat_corto = categoria.replace("CAMAS-", "").replace("CAMILLAS-", "")

                datos_tabla.append(
                    [
                        cat_corto,
                        f"{capacidad:,}",
                        f"{ocupacion:,}",
                        f"{disponible:,}",
                        f"{porcentaje}%",
                        str(sedes),
                        estado,
                    ]
                )

        # Total Federico Lleras
        total_capacidad = int(df_federico["cantidad_ci_TOTAL_REPS"].sum())
        total_ocupacion = int(df_federico["total_ingresos_paciente_servicio"].sum())
        total_disponible = total_capacidad - total_ocupacion
        total_porcentaje = (
            round((total_ocupacion / total_capacidad * 100), 1)
            if total_capacidad > 0
            else 0
        )
        total_sedes = df_federico["nombre_sede_prestador"].nunique()

        estado_general = self._determinar_estado(total_porcentaje)

        datos_tabla.append(
            [
                "TOTAL FEDERICO LLERAS",
                f"{total_capacidad:,}",
                f"{total_ocupacion:,}",
                f"{total_disponible:,}",
                f"{total_porcentaje}%",
                str(total_sedes),
                estado_general,
            ]
        )

        headers = [
            "Tipo de Servicio",
            "Capacidad\nInstalada",
            "Ocupación\nActual",
            "Disponible",
            "% Ocupación",
            "Sedes",
            "Estado",
        ]

        return [headers] + datos_tabla

    def _crear_estilo_tabla_con_colores(self):
        """Crear estilo de tabla con colores en columna estado."""
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
                (
                    "ALIGN",
                    (0, 1),
                    (0, -1),
                    "LEFT",
                ),  # Nombres IPS alineados a la izquierda
            ]
        )

    def _aplicar_colores_estado(self, tabla_style, tabla_data, col_estado_index):
        """Aplicar colores en la columna de estado."""
        for i, fila in enumerate(tabla_data[1:], 1):  # Saltar encabezado
            if len(fila) > col_estado_index:
                estado = fila[col_estado_index]
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
        """Generar informe completo con fecha de registro y firmas institucionales."""
        if archivo_salida is None:
            timestamp = self.fecha_procesamiento.strftime("%Y%m%d_%H%M%S")
            archivo_salida = f"informe_hospitalario_completo_{timestamp}.pdf"

        print(f"📄 Generando informe hospitalario completo: {archivo_salida}")

        # Extraer fecha de registro del Excel
        fecha_registro = self._extraer_fecha_registro()

        # Márgenes ajustados para evitar superposición
        header_height_inches = 95 / 72.0  # Convertir puntos a inches (≈ 1.32 inches)

        doc = HospitalDocTemplate(
            archivo_salida,
            fecha_registro=fecha_registro,  # Pasar fecha de registro
            pagesize=A4,
            rightMargin=0.4 * inch,
            leftMargin=0.4 * inch,
            topMargin=(header_height_inches + 0.25) * inch,  # Margen superior aumentado
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
            spaceBefore=6,  # Espaciado antes del título
            textColor=colors.HexColor(COLORS["primary"]),
            fontName="Helvetica-Bold",
        )

        texto_normal = ParagraphStyle(
            "TextoNormal",
            parent=estilos["Normal"],
            fontSize=9,
            spaceAfter=8,
            spaceBefore=4,  # Espaciado antes del texto
            alignment=TA_JUSTIFY,
        )

        texto_small = ParagraphStyle(
            "TextoSmall",
            parent=estilos["Normal"],
            fontSize=8,
            spaceAfter=6,
            spaceBefore=3,  # Espaciado antes del texto pequeño
            alignment=TA_JUSTIFY,
        )

        # ======================================================================
        # PORTADA - Con espaciado adicional para evitar superposición
        # ======================================================================
        elementos.append(Spacer(1, 0.3 * inch))  # Espaciador aumentado
        elementos.append(
            Paragraph("INFORME DE CAPACIDAD HOSPITALARIA", titulo_principal)
        )

        # EXPLICACIÓN DE UMBRALES AL INICIO
        elementos.append(Spacer(1, 0.3 * inch))
        elementos.append(Paragraph("UMBRALES DE ESTADO DE OCUPACIÓN", titulo_seccion))

        explicacion_umbrales = f"""
        • <b>🟢 NORMAL:</b> Menos del {UMBRALES['advertencia']}% de ocupación<br/>
        • <b>🟡 ADVERTENCIA:</b> Entre {UMBRALES['advertencia']}% y {UMBRALES['critico']-1}% de ocupación<br/>
        • <b>🔴 CRÍTICO:</b> {UMBRALES['critico']}% o más de ocupación<br/><br/>
        """

        elementos.append(Paragraph(explicacion_umbrales, texto_normal))
        elementos.append(PageBreak())

        # ======================================================================
        # 1. RESUMEN DEPARTAMENTAL
        # ======================================================================
        elementos.append(
            Spacer(1, 0.1 * inch)
        )  # CORRECCIÓN: Espaciador inicial en cada página
        elementos.append(
            Paragraph("1. RESUMEN DEPARTAMENTO DEL TOLIMA", titulo_seccion)
        )

        tabla_departamental = self._crear_tabla_resumen_departamental()
        if tabla_departamental:
            tabla_style = self._crear_estilo_tabla_con_colores()
            self._aplicar_colores_estado(
                tabla_style, tabla_departamental, 7
            )  # Columna 7 es Estado

            tabla_pdf = Table(tabla_departamental, repeatRows=1)
            tabla_pdf.setStyle(tabla_style)
            elementos.append(tabla_pdf)

        elementos.append(PageBreak())

        # ======================================================================
        # 2. IBAGUÉ
        # ======================================================================
        elementos.append(Spacer(1, 0.1 * inch))  # Espaciador inicial
        elementos.append(Paragraph("2. IBAGUÉ", titulo_seccion))
        elementos.append(Spacer(1, 0.1 * inch))

        tabla_ibague = self._crear_tabla_ips_por_municipio("Ibagué")
        if tabla_ibague:
            tabla_style = self._crear_estilo_tabla_con_colores()
            self._aplicar_colores_estado(
                tabla_style, tabla_ibague, 5
            )  # Columna 5 es Estado

            tabla_pdf = Table(tabla_ibague, repeatRows=1)
            tabla_pdf.setStyle(tabla_style)
            elementos.append(tabla_pdf)
        else:
            elementos.append(
                Paragraph("⚠️ No se encontraron datos para Ibagué", texto_normal)
            )

        elementos.append(PageBreak())

        # ======================================================================
        # 3. OTROS MUNICIPIOS
        # ======================================================================
        elementos.append(Spacer(1, 0.1 * inch))
        elementos.append(Paragraph("3. OTROS MUNICIPIOS DEL TOLIMA", titulo_seccion))

        # Obtener TODOS los municipios excepto Ibagué
        otros_municipios = [
            m for m in self.df["municipio_sede_prestador"].unique() if m != "Ibagué"
        ]
        otros_municipios.sort()

        print(f"📋 Procesando {len(otros_municipios)} municipios...")

        for i, municipio in enumerate(otros_municipios):
            if i > 0 and i % 4 == 0:  # Nueva página cada 4 municipios
                elementos.append(PageBreak())
                elementos.append(Spacer(1, 0.1 * inch))  # Espaciador tras PageBreak

            elementos.append(Paragraph(f"3.{i+1}. {municipio.upper()}", titulo_seccion))

            tabla_municipio = self._crear_tabla_ips_por_municipio(municipio)
            if tabla_municipio:
                tabla_style = self._crear_estilo_tabla_con_colores()
                self._aplicar_colores_estado(
                    tabla_style, tabla_municipio, 5
                )  # Columna 5 es Estado

                tabla_pdf = Table(tabla_municipio, repeatRows=1)
                tabla_pdf.setStyle(tabla_style)
                elementos.append(tabla_pdf)
                elementos.append(Spacer(1, 0.1 * inch))
            else:
                elementos.append(
                    Paragraph(
                        f"⚠️ No se encontraron datos para {municipio}", texto_small
                    )
                )
                elementos.append(Spacer(1, 0.05 * inch))

        elementos.append(PageBreak())

        # ======================================================================
        # 4. HOSPITAL FEDERICO LLERAS (TABLA FINAL)
        # ======================================================================
        elementos.append(Spacer(1, 0.1 * inch))
        elementos.append(
            Paragraph("4. HOSPITAL FEDERICO LLERAS ACOSTA", titulo_seccion)
        )
        elementos.append(Spacer(1, 0.15 * inch))

        tabla_federico = self._crear_tabla_federico_lleras_final()
        if tabla_federico:
            # Estilo especial para Federico Lleras
            tabla_style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLORS["danger"])),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -2), colors.beige),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E3F2FD")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )

            self._aplicar_colores_estado(
                tabla_style, tabla_federico, 6
            )  # Columna 6 es Estado

            tabla_pdf = Table(tabla_federico, repeatRows=1)
            tabla_pdf.setStyle(tabla_style)
            elementos.append(tabla_pdf)

            # Información adicional
            elementos.append(Spacer(1, 0.2 * inch))

            # Calcular participación
            total_departamento = self.df["cantidad_ci_TOTAL_REPS"].sum()
            df_federico = self.df[
                self.df["nombre_prestador"].str.contains(
                    "FEDERICO LLERAS ACOSTA", case=False, na=False
                )
            ]
            total_federico = (
                df_federico["cantidad_ci_TOTAL_REPS"].sum()
                if not df_federico.empty
                else 0
            )
            participacion = (
                round((total_federico / total_departamento * 100), 1)
                if total_departamento > 0
                else 0
            )

        # ======================================================================
        # SECCIÓN DE FIRMAS INSTITUCIONALES
        # ======================================================================
        elementos.extend(self._crear_seccion_firmas())

        # Construir documento
        try:
            doc.build(elementos)
            print(f"✅ Informe hospitalario completo generado: {archivo_salida}")
            print(f"📅 Fecha de registro utilizada: {fecha_registro}")
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
    print("=" * 72)

    if len(sys.argv) < 2:
        print("📋 USO DEL PROGRAMA:")
        print("   python hospital_report.py <archivo_excel>")
        print("")
        print("📊 EJEMPLO:")
        print("   python hospital_report.py Detalle_Ocupacion_CI.xlsx")
        print("")
        return

    archivo_excel = sys.argv[1]

    if not os.path.exists(archivo_excel):
        print(f"❌ Error: El archivo '{archivo_excel}' no existe.")
        return

    # Crear generador
    generador = HospitalCompletoGenerator()

    try:
        # Cargar TODOS los datos
        if not generador.cargar_datos(archivo_excel):
            print("❌ Error al cargar los datos.")
            return

        # Generar informe completo
        archivo_generado = generador.generar_informe_completo()

        if archivo_generado:
            print("🎉" + "=" * 70)
            print("✅ INFORME HOSPITALARIO COMPLETO GENERADO EXITOSAMENTE")
            print(f"📄 Archivo: {archivo_generado}")
            print(f"📊 Registros procesados: {len(generador.df):,}")

            # Estadísticas finales
            total_capacidad = generador.df["cantidad_ci_TOTAL_REPS"].sum()
            total_ocupacion = generador.df["total_ingresos_paciente_servicio"].sum()
            porcentaje_general = (
                round((total_ocupacion / total_capacidad * 100), 1)
                if total_capacidad > 0
                else 0
            )

            print(
                f"   🏘️ Municipios incluidos: {generador.df['municipio_sede_prestador'].nunique()}"
            )
            print(f"   🏥 IPS analizadas: {generador.df['nombre_prestador'].nunique()}")
            print(f"   📋 Categorías de servicios: {len(generador.todas_categorias)}")
            print(f"   🎯 Capacidad total: {total_capacidad:,} unidades")
            print(
                f"   📈 Ocupación total: {total_ocupacion:,} pacientes ({porcentaje_general}%)"
            )

            # Verificar Federico Lleras
            df_federico = generador.df[
                generador.df["nombre_prestador"].str.contains(
                    "FEDERICO LLERAS ACOSTA", case=False, na=False
                )
            ]
            if not df_federico.empty:
                print(f"   🏥 Hospital Federico Lleras: ✅ ENCONTRADO")
            else:
                print(f"   🏥 Hospital Federico Lleras: ❌ NO ENCONTRADO")

            print("=" * 72)
            print("📋 INFORME INCLUYE:")
            print("   • Fecha de registro desde Excel")
            print("   • Logo institucional Gobernacion.png")
            print("   • Header sin superposición de texto")
            print("   • Resumen con todas las categorías del Excel")
            print("   • Ibagué (prioritario) con todas sus IPS")
            print("   • Todos los municipios con sus respectivas IPS")
            print("   • Tabla final específica Hospital Federico Lleras")
            print("   • Firmas institucionales al final del documento")
            print("=" * 72)
        else:
            print("❌ Error al generar el informe.")

    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
