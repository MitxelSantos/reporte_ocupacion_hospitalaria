# 🏥 Sistema Optimizado de Monitoreo UCI - Tolima

**Generador de Informes UCI Especializado**  
*Secretaría de Salud del Tolima*

---

## 📋 Descripción

Sistema especializado para el monitoreo y análisis de **Unidades de Cuidados Intensivos (UCI)** del departamento del Tolima. Genera informes ejecutivos enfocados en la toma de decisiones críticas para el manejo de capacidad UCI.

### ✨ Características Principales

- **🎯 Enfoque UCI Específico**: Monitoreo especializado de UCIs
- **📊 Dos Tipos de Informes**: Simple (estilo Word) y Dashboard (múltiples visualizaciones)
- **🏥 Análisis Federico Lleras**: Sección específica del hospital de referencia
- **🚨 Alertas Automáticas**: Sistema de alertas UCI por umbrales críticos
- **📈 Categorización Precisa**: Basada en datos reales del sistema REPS
- **🖼️ Logo Institucional**: Integración del logo de la Gobernación del Tolima

## 🎯 Categorías UCI Analizadas

| Categoría | Descripción | Datos REPS |
|-----------|-------------|------------|
| **UCI Adulto** | Unidad de Cuidados Intensivos para Adultos | CAMAS-Cuidado Intensivo Adulto + CAMAS-Intensiva Adultos |
| **UCI Intermedio Adulto** | Unidad de Cuidados Intermedios para Adultos | CAMAS-Cuidado Intermedio Adulto |
| **UCI Pediátrico** | Unidad de Cuidados Intensivos Pediátricos | CAMAS-Cuidado Intensivo Pediátrico |
| **UCI Intermedio Pediátrico** | Unidad de Cuidados Intermedios Pediátricos | CAMAS-Cuidado Intermedio Pediátrico |
| **Hospitalización General** | Camas de Hospitalización General | CAMAS-Adultos + CAMAS-Pediátrica |
| **Observación/Urgencias** | Camillas de Observación y Urgencias | CAMILLAS-Observación (todas) |

## 🚨 Umbrales de Alerta UCI

- **🟢 Normal**: < 70% de ocupación
- **🟡 Advertencia**: 70% - 84% de ocupación  
- **🔴 Crítico**: ≥ 85% de ocupación

## 🛠️ Instalación

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación Rápida

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd hospital-uci-optimized

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

### Comandos Básicos

```bash
# Generar ambos informes (recomendado)
python hospital_uci_optimized.py datos.xlsx ambos

# Generar solo informe simple (estilo Word)
python hospital_uci_optimized.py datos.xlsx simple

# Generar solo dashboard (visualizaciones múltiples)
python hospital_uci_optimized.py datos.xlsx dashboard
```

### Ejemplos Específicos

```bash
# Análisis completo con ambos tipos de informe
python hospital_uci_optimized.py Detalle_Ocupacion_CI.xlsx ambos

# Solo informe ejecutivo simple
python hospital_uci_optimized.py Detalle_Ocupacion_CI.xlsx simple

# Solo dashboard con múltiples visualizaciones
python hospital_uci_optimized.py Detalle_Ocupacion_CI.xlsx dashboard
```

## 📊 Estructura de Informes

### 🔸 Informe Simple (Estilo Word)

1. **Portada Institucional**
   - Logo de la Gobernación del Tolima
   - Fecha y hora de generación

2. **Resumen Ejecutivo UCI**
   - Situación general UCI departamental
   - Estadísticas por categoría UCI
   - Gráficos de barras simples

3. **Análisis UCI - Ibagué**
   - Participación de Ibagué en UCI departamental
   - Detalle por categoría UCI
   - Comparativas con el departamento

4. **Análisis Específico - Hospital Federico Lleras Acosta**
   - Participación en UCI departamental e Ibagué
   - Detalle UCI por categoría
   - Estado específico por servicio

5. **Alertas UCI y Recomendaciones**
   - Alertas automáticas por umbrales
   - Recomendaciones para toma de decisiones

### 🔸 Informe Dashboard (Múltiples Visualizaciones)

1. **Dashboard Principal**
   - Panel resumen general UCI
   - Alertas críticas en tiempo real
   - Distribución por municipios
   - Gráficos tipo dona por categoría
   - Tendencias y comparativas

2. **Análisis Detallado**
   - Misma estructura que informe simple
   - Gráficos más complejos y detallados

## 📁 Estructura de Archivos

```
hospital-uci-optimized/
├── hospital_uci_optimized.py  # Sistema principal optimizado
├── requirements.txt           # Dependencias Python
├── README.md                  # Esta documentación
├── .gitignore                # Archivos ignorados por Git
├── ejemplos/                  # Ejemplos de uso
│   └── Detalle_Ocupacion_CI.xlsx
├── docs/                      # Documentación adicional
│   ├── manual_usuario.md
│   └── especificaciones_uci.md
└── assets/                    # Recursos
    └── logo_tolima.png        # Logo institucional
```

## 📋 Formato de Datos de Entrada

El archivo Excel debe contener las siguientes columnas obligatorias:

| Columna | Descripción | Tipo |
|---------|-------------|------|
| `municipio_sede_prestador` | Municipio de la sede | Texto |
| `nombre_prestador` | Nombre del prestador de salud | Texto |
| `nivel_de_atencion_prestador` | Nivel de atención (1, 2, 3) | Numérico |
| `nombre_sede_prestador` | Nombre de la sede específica | Texto |
| `nombre_capacidad_instalada` | Tipo de capacidad (UCI, camas, camillas) | Texto |
| `cantidad_ci_TOTAL_REPS` | Capacidad total disponible | Numérico |
| `total_ingresos_paciente_servicio` | Pacientes ingresados (ocupación) | Numérico |

### Tipos de Capacidad Reconocidos

- `CAMAS-Cuidado Intensivo Adulto`
- `CAMAS-Cuidado Intensivo Pediátrico`
- `CAMAS-Cuidado Intermedio Adulto`
- `CAMAS-Cuidado Intermedio Pediátrico`
- `CAMAS-Intensiva Adultos`
- `CAMAS-Adultos`
- `CAMAS-Pediátrica`
- `CAMILLAS-Observación Adultos Hombres`
- `CAMILLAS-Observación Adultos Mujeres`
- `CAMILLAS-Observación Pediátrica`

## 🔧 Configuración

### Colores Institucionales UCI

```python
COLORS = {
    "primary": "#7D0F2B",        # Rojo institucional Tolima
    "secondary": "#F2A900",      # Amarillo dorado
    "uci_adulto": "#E53E3E",     # Rojo para UCI Adulto
    "uci_pediatrico": "#3182CE", # Azul para UCI Pediátrico
    "uci_intermedio": "#38A169", # Verde para UCI Intermedio
    "hospitalizacion": "#805AD5", # Púrpura para Hospitalización
    "observacion": "#F56500"     # Naranja para Observación
}
```

### Umbrales de Alertas UCI

```python
UMBRALES_UCI = {
    "critico": 85,      # ≥85% crítico para UCI
    "advertencia": 70,  # 70-84% advertencia para UCI
    "normal": 0         # <70% normal
}
```

## 📈 Salidas del Sistema

### Archivos Generados

- **`informe_uci_simple_YYYYMMDD_HHMMSS.pdf`**: Informe ejecutivo simple
- **`informe_uci_dashboard_YYYYMMDD_HHMMSS.pdf`**: Dashboard con visualizaciones múltiples

### Estadísticas Mostradas

```
📊 Estadísticas procesadas:
   🏥 Total registros: 368
   🏘️ Municipios: 47
   🏛️ Prestadores: 69
   🎯 Capacidad UCI: 356 camas
   📈 Ocupación UCI: 88 pacientes (24.7%)
   🏥 Hospital Federico Lleras: ✅ ENCONTRADO
```

## 🤝 Contribución

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad-uci`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad UCI'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad-uci`)
5. Crea un Pull Request

## 📝 Changelog

### Versión 2.0.0 (Optimizada - Actual)
- ✅ **Enfoque UCI específico** según datos reales REPS
- ✅ **Dos tipos de informes**: Simple y Dashboard
- ✅ **Categorización precisa** basada en datos Excel
- ✅ **Sección específica Hospital Federico Lleras**
- ✅ **Umbrales UCI especializados** (85% crítico vs 90% general)
- ✅ **Alertas automáticas** para toma de decisiones
- ✅ **Gráficos optimizados** estilo Word y Dashboard
- ✅ **Integración logo institucional**

### Versión 1.0.0 (Original)
- ✅ Análisis general por servicios y niveles
- ✅ Generación PDF básica
- ✅ Soporte para datos COVID-19

## 🐛 Reporte de Problemas

Si encuentras algún problema:

1. Revisa los [issues existentes](../../issues)
2. Si no existe, crea un nuevo issue con:
   - Descripción detallada del problema UCI
   - Pasos para reproducir
   - Archivo Excel de ejemplo (sin datos sensibles)
   - Tipo de informe que intentabas generar

## 📞 Soporte Técnico

Para soporte técnico o consultas sobre UCI:

- **Desarrollador**: Ing. José Miguel Santos
- **Institución**: Secretaría de Salud del Tolima
- **Especialidad**: Sistemas de Monitoreo UCI
- **Email**: [contacto institucional]

## 🔐 Seguridad y Privacidad

- ⚠️ **Datos Sensibles UCI**: No incluir archivos Excel con datos reales en el repositorio
- 🔒 **Confidencialidad Médica**: Los reportes UCI pueden contener información crítica de salud
- 🚫 **Exclusiones**: El `.gitignore` está configurado para excluir datos hospitalarios sensibles
- 🏥 **Uso Autorizado**: Solo para personal autorizado de la Secretaría de Salud

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

**© 2025 - Secretaría de Salud del Tolima**  
*Sistema Optimizado de Monitoreo UCI*

**🎯 Enfoque Especializado UCI | 📊 Informes Ejecutivos | 🚨 Alertas en Tiempo Real**