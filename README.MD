# 🏥 Sistema de Análisis de Capacidad Hospitalaria - Tolima

**Generador de Informes Final Optimizado de Capacidad Hospitalaria**  
*Secretaría de Salud del Tolima*

---

## 📋 Descripción

Sistema integral para el análisis y generación de informes detallados sobre la capacidad hospitalaria del departamento del Tolima. Esta herramienta procesa datos de ocupación hospitalaria y genera reportes PDF profesionales con análisis exhaustivos, gráficos optimizados y alertas críticas.

### ✨ Características Principales

- **🛏️ Análisis CAMAS vs CAMILLAS**: Distinción completa en todos los análisis
- **📊 Gráficos Optimizados**: Visualizaciones de alta calidad con mayor altura vertical
- **📋 Alertas en Tabla**: Formato estructurado para alertas críticas
- **🗺️ Análisis Territorial**: Cobertura completa de municipios y prestadores
- **🏥 Detalle Institucional**: Análisis específico por prestador y sede
- **📈 Reportes PDF**: Documentos profesionales listos para presentación

## 🛠️ Tecnologías

- **Python 3.8+**
- **pandas**: Procesamiento de datos
- **matplotlib**: Generación de gráficos
- **numpy**: Cálculos numéricos
- **reportlab**: Generación de PDF
- **openpyxl**: Lectura de archivos Excel

## 📦 Instalación

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación de Dependencias

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd hospital-capacity-analysis

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🚀 Uso

### Comando Básico

```bash
python hospital_report.py archivo_datos.xlsx [archivo_salida.pdf]
```

### Ejemplos de Uso

```bash
# Generar informe con nombre automático
python hospital_report.py datos_hospitalarios_2024.xlsx

# Generar informe con nombre específico
python hospital_report.py datos_hospitalarios_2024.xlsx informe_enero_2024.pdf

# Ver ayuda y características del sistema
python hospital_report.py
```

## 📊 Estructura del Informe

El informe generado incluye las siguientes secciones:

### 1. 📈 Resumen Ejecutivo General
- Estadísticas generales del Tolima
- Análisis CAMAS vs CAMILLAS
- Indicadores clave de ocupación

### 2. 📊 Análisis Gráfico Optimizado
- Gráficos de capacidad y ocupación
- Comparativas por municipios
- Visualizaciones por tipo de capacidad

### 3. 🚨 Alertas Críticas Detalladas
- Municipios con ocupación crítica (≥90%)
- Sedes específicas en estado crítico
- Tipos de capacidad con alta ocupación

### 4. 🛏️ Análisis por Tipos de Capacidad
- Distinción completa CAMAS/CAMILLAS
- UCI, Cuidado Intermedio, Hospitalización
- Observación por grupos etarios

### 5. 🏛️ Análisis Detallado de Ibagué
- Capital departamental con análisis específico
- Desglose por tipo de capacidad
- Comparativas con el resto del departamento

### 6. 🗺️ Análisis Municipal y de Prestadores
- Todos los municipios del Tolima
- Prestadores específicos por municipio
- Instituciones públicas vs privadas

## 📁 Estructura de Archivos

```
hospital-capacity-analysis/
├── hospital_report.py          # Script principal
├── requirements.txt            # Dependencias Python
├── README.md                   # Documentación
├── .gitignore                 # Archivos ignorados por Git
├── LICENSE                    # Licencia del proyecto
├── examples/                  # Ejemplos de uso
│   └── sample_data.xlsx       # Datos de ejemplo
└── docs/                      # Documentación adicional
    ├── manual_usuario.md      # Manual de usuario
    └── especificaciones.md    # Especificaciones técnicas
```

## 📋 Formato de Datos de Entrada

El archivo Excel debe contener las siguientes columnas:

| Columna | Descripción | Tipo |
|---------|-------------|------|
| `fecha_registro` | Fecha del registro | Fecha |
| `municipio_sede_prestador` | Municipio de la sede | Texto |
| `nombre_prestador` | Nombre del prestador de salud | Texto |
| `nombre_sede_prestador` | Nombre de la sede específica | Texto |
| `numero_sede` | Número identificador de la sede | Numérico |
| `nombre_capacidad_instalada` | Tipo de capacidad (camas/camillas) | Texto |
| `cantidad_ci_TOTAL_REPS` | Capacidad total disponible | Numérico |
| `ocupacion_ci_confirmado_covid19` | Ocupación COVID-19 confirmado | Numérico |
| `ocupacion_ci_sospechoso_covid19` | Ocupación COVID-19 sospechoso | Numérico |
| `ocupacion_ci_no_covid19` | Ocupación no COVID-19 | Numérico |
| `cantidad_ci_disponibles` | Capacidad disponible | Numérico |
| `total_ingresos_paciente_servicio` | Total de pacientes ingresados | Numérico |
| `naturaleza_juridica` | Tipo de institución | Texto |

## 🔧 Configuración

### Colores Institucionales

El sistema utiliza los colores oficiales de la Secretaría de Salud del Tolima:

```python
COLORS = {
    "primary": "#7D0F2B",      # Rojo institucional
    "secondary": "#F2A900",     # Amarillo dorado
    "accent": "#5A4214",        # Marrón
    "success": "#509E2F",       # Verde
    "warning": "#F7941D",       # Naranja
    "white": "#FFFFFF",         # Blanco
}
```

### Umbrales de Alertas

- **🟢 Normal**: < 70% de ocupación
- **🟡 Advertencia**: 70% - 89% de ocupación
- **🔴 Crítico**: ≥ 90% de ocupación

## 🤝 Contribución

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📝 Changelog

### Versión 1.0.0 (Actual)
- ✅ Análisis completo CAMAS vs CAMILLAS
- ✅ Gráficos optimizados con mayor altura
- ✅ Alertas críticas en formato tabla
- ✅ Análisis detallado por municipio y prestador
- ✅ Generación de PDF profesional
- ✅ Soporte para datos COVID-19 y no COVID-19

## 🐛 Reporte de Problemas

Si encuentras algún problema o tienes sugerencias:

1. Revisa los [issues existentes](../../issues)
2. Si no existe, crea un nuevo issue con:
   - Descripción detallada del problema
   - Pasos para reproducir
   - Archivos de ejemplo (sin datos sensibles)
   - Versión de Python y SO

## 📞 Soporte

Para soporte técnico o consultas:

- **Desarrollador**: Ing. José Miguel Santos
- **Institución**: Secretaría de Salud del Tolima
- **Email**: [contacto institucional]

## 🔐 Seguridad y Privacidad

- ⚠️ **Datos Sensibles**: No incluir archivos Excel con datos reales en el repositorio
- 🔒 **Confidencialidad**: Los reportes generados pueden contener información sensible
- 🚫 **Exclusiones**: El `.gitignore` está configurado para excluir datos hospitalarios

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

**© 2025 - Secretaría de Salud del Tolima**  
*Sistema Final Optimizado de Monitoreo Hospitalario*