# Asistente Inteligente de Onboarding (TFG)

Este repositorio contiene el código fuente de una Prueba de Concepto (PoC) para un Asistente Inteligente de Onboarding, basado en RAG y una arquitectura multiagente (LangGraph). 

El proyecto resuelve el problema organizativo de la integración de nuevos desarrolladores, unificando la resolución de dudas sobre código, la validación de normativas internas y consultas de Recursos Humanos.

## Requisitos previos
- Python 3.10 o superior.
- Una clave API válida de OpenAI.
- Git instalado en el sistema.

## Guía de instalación y ejecución para el Tribunal

Para poder probar el sistema localmente, sigue estos pasos:

### 1. Clonar el repositorio
Abre una terminal y ejecuta:
```bash
git clone https://github.com/scy2-ua/asistente-onboarding-tfg.git
cd asistente-onboarding-tfg
```

### 2. Crear y activar un entorno virtual
Es recomendable aislar las dependencias del proyecto creando un entorno virtual:
```bash
python -m venv venv

# Activación en Windows:
venv\Scripts\activate

# Activación en macOS/Linux:
source venv/bin/activate
```

### 3. Instalar las dependencias
Con el entorno virtual activado, instala las librerías necesarias ejecutando:
```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno
El sistema requiere acceso a los modelos de OpenAI para funcionar.
1. Busca el archivo llamado `.env.example` en la raíz del proyecto.
2. Renómbralo a `.env`.
3. Ábrelo con cualquier editor de texto y sustituye el texto de ejemplo por tu clave real:
   ```env
   OPENAI_API_KEY="sk-..."
   ```

### 5. Ejecutar la aplicación
Una vez configurado todo, lanza la interfaz de usuario con Streamlit:
```bash
streamlit run app.py
```
El navegador se abrirá automáticamente en `http://localhost:8501` con la interfaz del asistente lista para usar.# asistente-onboarding-tfg
Código fuente del Trabajo de Fin de Grado: Asistente Inteligente de Onboarding con RAG y arquitectura multiagente
