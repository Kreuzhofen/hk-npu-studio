# Snapdragon AI Studio – Phoenix Engine
## Manual de usuario – Versión 2.0 RC2A

> **Proyecto independiente de código abierto para Windows en Snapdragon.**  
> Snapdragon AI Studio no es un producto oficial de Qualcomm Technologies, Inc. y no está patrocinado ni respaldado por Qualcomm.

---

## 1. Bienvenido

Snapdragon AI Studio es una aplicación de escritorio para la generación local de imágenes con IA en equipos Windows 11 ARM64 con procesadores Snapdragon. **Phoenix Engine** se encarga de la gestión de modelos, la preparación y la ejecución de las canalizaciones de IA compatibles.

RC2A pone especial énfasis en un flujo guiado: **Instalar → seleccionar un modelo → generar una imagen.** Los detalles técnicos deben permanecer en segundo plano tanto como sea posible durante el uso normal.

La generación de imágenes se ejecuta localmente en el PC. Una vez configurado el modelo necesario, la generación propiamente dicha no requiere, por regla general, un servicio de generación de imágenes en la nube.

---

## 2. Requisitos del sistema

### Plataforma compatible

- Windows 11 ARM64
- Qualcomm Snapdragon X Plus o Snapdragon X Elite como plataforma objetivo principal
- Se recomiendan controladores actuales de Windows y Qualcomm
- Espacio SSD libre suficiente para los modelos que se deseen utilizar

### Memoria y almacenamiento

Los requisitos reales dependen del modelo utilizado. Los modelos grandes necesitan bastante más espacio que la propia aplicación. Durante la configuración de Stable Diffusion 3.5 Medium se descargan varios gigabytes; la descarga del modelo de Qualcomm es actualmente de aproximadamente **3,24 GB**, además de los archivos de instalación y trabajo que se generan.

### Conexión a Internet

Se necesita una conexión a Internet cuando se descargan por primera vez los componentes o modelos necesarios. Después de una instalación correcta, las generaciones de imágenes compatibles se ejecutan localmente.

---

## 3. Instalar RC2A

1. Descarga el instalador ARM64 actual desde la versión oficial de Snapdragon AI Studio en GitHub.
2. Ejecuta `SnapdragonAIStudio-2.0.0-rc.2a-ARM64-Setup.exe`.
3. Sigue el asistente de instalación de Windows.
4. Inicia **Snapdragon AI Studio** desde el menú Inicio o desde el acceso directo creado.

> **Windows SmartScreen:** Windows puede mostrar una advertencia para una versión que todavía no sea ampliamente reconocida o no tenga una firma comercial. Utiliza únicamente instaladores obtenidos desde el repositorio oficial del proyecto.

Para el uso normal del instalador publicado no es necesario instalar Python por separado.

---

## 4. Primer inicio

RC2A guía a los nuevos usuarios durante la configuración inicial de forma mucho más clara que los candidatos de versión anteriores.

La página de inicio muestra el estado actual de configuración. Si todavía no hay ningún modelo utilizable configurado, la aplicación te guía hasta el Gestor de modelos. Tras completar correctamente la configuración, se actualiza el estado de disponibilidad y puedes pasar directamente a la primera generación de imágenes.

### Flujo básico

1. Inicia Snapdragon AI Studio.
2. Abre el Gestor de modelos.
3. Selecciona el modelo compatible que desees.
4. Inicia el proceso de instalación ofrecido.
5. Deja que la instalación y la validación terminen por completo.
6. Activa el modelo o espera a la activación automática.
7. Cambia a la generación de imágenes.

En el flujo guiado normal no necesitas seleccionar por separado componentes internos de ONNX, QNN o del modelo.

---

## 5. Gestor de modelos

El Gestor de modelos muestra los modelos conocidos por Snapdragon AI Studio y su estado actual.

Según el modelo y su estado de desarrollo, puede aparecer como instalado, no instalado, disponible o experimental.

### Instalado

El paquete de modelo necesario se ha encontrado y validado correctamente.

### Activo

El modelo está seleccionado actualmente para la generación de imágenes.

### No instalado

Los archivos necesarios del modelo todavía no se han configurado completamente.

### Experimental / En desarrollo

Estos modelos no forman parte del mismo flujo estable que los modelos publicados. Las entradas experimentales pueden tener requisitos adicionales o no estar todavía destinadas al uso cotidiano.

> **Recomendación:** Para empezar, utiliza un modelo que aparezca expresamente como disponible y compatible en el Gestor de modelos.

---

## 6. Instalar modelos

RC2A utiliza distintas fuentes y métodos de instalación según el modelo. El Gestor de modelos intenta ocultar estas diferencias y ofrecer un flujo guiado.

### Stable Diffusion 1.5

Stable Diffusion 1.5 es una opción compacta para iniciarse en la generación local de imágenes y resulta especialmente adecuada para flujos rápidos de 512×512. Con una variante NPU compatible, Phoenix se encarga de la validación y activación necesarias del paquete.

### Stable Diffusion 2.1

Stable Diffusion 2.1 también está disponible como vía de generación orientada a Snapdragon/Qualcomm. La instalación y activación se realizan mediante el Gestor de modelos según la fuente configurada para el modelo.

### Stable Diffusion 3.5 Medium

RC2A incluye un proceso de configuración mucho más automatizado para **Stable Diffusion 3.5 Medium mediante Qualcomm QAI AppBuilder**. Este flujo se describe por separado en el siguiente capítulo.

---

## 7. Configurar Stable Diffusion 3.5 Medium

La configuración de SD3.5 es más extensa que la de paquetes de modelos más pequeños. Por ello, Phoenix automatiza tantos pasos como sea posible.

### Lo que Phoenix realiza automáticamente

El flujo guiado puede:

1. localizar el ZIP necesario de Qualcomm QAI AppBuilder,
2. preparar y extraer el archivo,
3. preparar los componentes de Python necesarios para la configuración,
4. ejecutar el script de Qualcomm para SD3.5,
5. descargar los archivos de modelo necesarios,
6. importar los archivos generados a Snapdragon AI Studio,
7. crear el manifiesto y la información de validación,
8. validar la instalación,
9. activar el modelo a continuación.

Durante el proceso, la ventana de instalación muestra el paso actual y el progreso.

### Qualcomm QAI AppBuilder

Este método utiliza el proyecto oficial QAI AppBuilder de Qualcomm. Phoenix busca el archivo ZIP esperado en la carpeta Descargas. Si no se encuentra automáticamente, la aplicación puede pedirte que selecciones el archivo ZIP.

El archivo ZIP del usuario no se elimina durante el proceso normal de instalación.

### Descarga del modelo

Durante la configuración, el script de Qualcomm descarga los archivos necesarios de SD3.5. La descarga es actualmente de aproximadamente **3,24 GB**. La velocidad y duración dependen de la conexión a Internet, el dispositivo de almacenamiento y el estado del sistema.

No cierres Snapdragon AI Studio durante este proceso y deja que la instalación termine por completo.

### Finalización

Después de la configuración, se validan los archivos del modelo y este queda disponible para Snapdragon AI Studio. El flujo de usuario correcto de RC2A se ha probado como una cadena completa:

**no instalado → configuración correcta en el primer intento → descarga de Qualcomm → importación/validación → activación → generación real de una imagen.**

---

## 8. Generar una imagen

Después de seleccionar un modelo instalado, cambia a la generación de imágenes.

1. Introduce una descripción de la imagen deseada en el campo **Prompt**.
2. Opcionalmente, introduce un **Negative Prompt**.
3. Revisa los parámetros de generación deseados.
4. Haz clic en **Generar**.
5. Espera a que Phoenix Engine complete la canalización.
6. La imagen terminada se muestra y se incorpora al historial o área de salida correspondiente.

El tiempo necesario depende en gran medida del modelo, la resolución, la configuración y el backend utilizado.

---

## 9. Prompt y Negative Prompt

### Prompt

El prompt describe **qué debe aparecer en la imagen**.

Ejemplo:

> Retrato de una astronauta, iluminación cinematográfica, detalles finos, estilo realista

Las indicaciones concretas sobre el motivo, el entorno, la iluminación, la perspectiva y el estilo ayudan al modelo a interpretar la solicitud.

### Negative Prompt

El Negative Prompt describe características no deseadas. Su efecto depende del modelo y de la canalización.

Ejemplo:

> borroso, anatomía incorrecta, texto, marca de agua

---

## 10. Parámetros de generación

Los parámetros disponibles dependen del modelo activo.

### Seed

La semilla influye en el estado aleatorio inicial de una generación. Una semilla fija facilita las comparaciones reproducibles. El modo aleatorio crea estados iniciales diferentes en nuevas ejecuciones.

### Steps

El número de pasos de denoising influye en el tiempo de cálculo y en el resultado. Más pasos no significan automáticamente una imagen mejor.

### CFG / Guidance

Este valor controla hasta qué punto la generación debe seguir el prompt. Los valores extremadamente altos pueden empeorar la calidad de la imagen.

### Resolución

Las resoluciones compatibles dependen del modelo y del backend. Utiliza preferentemente los ajustes previstos para el modelo seleccionado.

### Sampler / Scheduler

Cuando el backend activo lo permite, el scheduler influye en el proceso de denoising. No todas las combinaciones están previstas para todos los modelos.

---

## 11. Phoenix Boost

**Phoenix Boost** es una función de Snapdragon AI Studio para mejorar o ampliar los prompts antes de generar una imagen.

Existen dos modos fundamentalmente distintos.

### Deterministic Boost

El boost determinista local funciona sin un modelo de lenguaje adicional. Amplía el prompt mediante reglas reproducibles y puede utilizarse directamente.

### AI Boost

El AI Boost opcional utiliza un modelo de lenguaje ejecutado localmente para mejorar el prompt de forma más inteligente.

RC2A utiliza:

- **Ollama** como servicio local de modelos
- **Qwen2.5 3B** como modelo de lenguaje local previsto

Si Ollama o Qwen todavía no están disponibles, Phoenix Boost guía al usuario por la configuración necesaria. La descarga del modelo puede tardar algún tiempo.

Tras una instalación correcta, este boost funciona localmente en el ordenador. El prompt original no necesita enviarse a un servicio externo de optimización de prompts en la nube.

### Vista previa

Antes de generar la imagen, puedes revisar la versión del prompt creada por Phoenix Boost. Así queda claro qué descripción se entrega realmente a la canalización de imagen.

> Phoenix Boost es opcional. La generación normal de imágenes no debe depender de que Ollama o Qwen estén instalados.

---

## 12. ControlNet Canny

Con combinaciones de modelo/backend compatibles, **ControlNet Canny** puede utilizarse para conservar con mayor intensidad la estructura de una imagen existente en una nueva generación.

Flujo habitual:

1. Activa ControlNet Canny.
2. Selecciona la imagen de origen.
3. Revisa la vista previa de Canny.
4. Ajusta los umbrales de bordes si están disponibles.
5. Introduce el prompt.
6. Inicia la generación.

ControlNet no está disponible para todas las variantes de modelos. La interfaz se adapta a las capacidades del modelo activo.

---

## 13. Galería, historial y comparación

Snapdragon AI Studio ofrece vistas de imágenes e historial para revisar las imágenes generadas.

Según la vista, puedes:

- consultar generaciones anteriores,
- volver a abrir resultados,
- comparar imágenes,
- consultar información relevante de la generación.

La presentación exacta puede seguir evolucionando entre candidatos de versión.

---

## 14. Idioma y modos oscuro y claro

La interfaz de usuario admite:

- Alemán
- Inglés
- Español

También están disponibles los modos oscuro y claro. El idioma y la apariencia pueden cambiarse en la configuración de la aplicación.

---

## 15. Datos y modelos locales

Snapdragon AI Studio almacena localmente la configuración de la aplicación, los datos de trabajo y los modelos instalados.

Con una instalación normal mediante el instalador, los datos productivos de los modelos pueden encontrarse en el área local de la aplicación del usuario de Windows, por ejemplo:

```text
%LOCALAPPDATA%\Snapdragon AI Studio\models
```

Las rutas internas pueden variar entre las versiones de desarrollo y las versiones instaladas. **No muevas ni elimines manualmente los archivos de modelos** salvo que estés realizando deliberadamente un diagnóstico.

La aplicación valida las instalaciones de modelos mediante los archivos y metadatos esperados. Una eliminación o un traslado manual incompleto puede hacer que el modelo se detecte como no válido.

---

## 16. Privacidad y funcionamiento sin conexión

Uno de los objetivos centrales de Snapdragon AI Studio es la ejecución local de IA.

### Local

- Los prompts se procesan localmente para la generación de imágenes.
- Los modelos de imagen compatibles se ejecutan localmente en el PC.
- Las imágenes generadas permanecen almacenadas localmente.
- Phoenix Boost funciona localmente después de configurar Ollama/Qwen.

### Aun así, algunas tareas de configuración requieren Internet

“Local” no significa que toda la configuración pueda realizarse sin conexión. Las descargas de componentes de la aplicación, modelos, recursos de Qualcomm, Ollama o Qwen requieren inicialmente una conexión a Internet.

Tras completar la configuración, las funciones locales previstas pueden utilizarse sin un servicio de generación de imágenes en la nube.

---

## 17. Solución de problemas

### Un modelo aparece como “No instalado”

Abre el Gestor de modelos y utiliza el proceso de instalación previsto. No copies archivos de modelos al azar en carpetas internas.

### La instalación se interrumpió

Reinicia Snapdragon AI Studio y abre el Gestor de modelos. Según el modelo, Phoenix puede reutilizar datos completos existentes u ofrecer una nueva descarga.

### SD3.5 informa de archivos incompletos

Utiliza la opción de nueva configuración o descarga ofrecida por Phoenix. El instalador distingue entre datos de salida completos e incompletos de Qualcomm y no debe activar una fuente incompleta como modelo terminado.

### Qwen/Phoenix Boost no funciona inmediatamente después de instalarlo

Comprueba primero que Ollama se haya iniciado por completo y que Qwen2.5 3B esté instalado. Si el servicio local de Ollama acaba de configurarse, puede ser necesario reiniciar el componente correspondiente de la aplicación.

### La generación tarda mucho

Los modelos grandes y las resoluciones altas necesitan más tiempo. La preparación, la primera carga de un modelo y la carga general del sistema también influyen en la duración.

### La aplicación parece no responder

Durante fases largas de instalación o generación, espera primero al progreso mostrado. No cierres la aplicación durante una descarga activa del modelo salvo que aparezca un mensaje de error claro.

### Informar de un error

Para problemas reproducibles resulta útil incluir:

- versión de Snapdragon AI Studio
- versión de Windows
- dispositivo/procesador Snapdragon
- modelo utilizado
- pasos exactos hasta el error
- mensaje o captura de pantalla relevante
- archivos de registro correspondientes, si están disponibles

---

## 18. Desinstalación

Snapdragon AI Studio puede desinstalarse desde **Configuración de Windows → Aplicaciones → Aplicaciones instaladas**.

Ten en cuenta que los archivos grandes de modelos y los datos del usuario pueden almacenarse por separado según la estrategia de instalación y almacenamiento. Antes de eliminar algo manualmente, comprueba si deseas conservar las imágenes generadas o los modelos.

---

## 19. Preguntas frecuentes

### ¿Snapdragon AI Studio es un producto oficial de Qualcomm?

No. Snapdragon AI Studio es un proyecto independiente de código abierto.

### ¿Se envían mis prompts a un servicio de imágenes en la nube?

La generación de imágenes compatible está diseñada para ejecutarse localmente. Sin embargo, se necesita una conexión a Internet para descargar y configurar algunos componentes.

### ¿Tengo que instalar Python?

No para el uso normal del instalador publicado para Windows. Python 3.11 ARM64 es relevante principalmente para el desarrollo o la ejecución desde el código fuente. La configuración de SD3.5 gestiona su proceso previsto mediante Phoenix.

### ¿Tengo que instalar Ollama?

Solo si quieres utilizar el **Phoenix AI Boost** opcional. La generación normal de imágenes debe funcionar sin Ollama.

### ¿Qué modelo de lenguaje utiliza Phoenix AI Boost?

RC2A utiliza **Qwen2.5 3B** mediante Ollama.

### ¿Tengo que recopilar manualmente archivos individuales de Qualcomm para SD3.5?

El flujo de RC2A está diseñado para automatizar la configuración de Qualcomm en la medida de lo posible. El usuario no debería tener que seleccionar manualmente componentes internos individuales del modelo.

### ¿Puedo eliminar los modelos directamente de sus carpetas?

No se recomienda durante el uso normal. Utiliza los procesos previstos de gestión e instalación. Los cambios manuales pueden hacer que el estado guardado y los archivos reales difieran temporalmente.

### ¿Qué idiomas admite la interfaz?

Alemán, inglés y español.

### ¿Puedo utilizar Snapdragon AI Studio en equipos Intel o AMD?

El proyecto está diseñado para Windows 11 ARM64 en Snapdragon. Otras plataformas no forman parte del objetivo principal oficialmente previsto o validado.

---

## 20. Soporte e informes de errores

Repositorio del proyecto:

`https://github.com/Kreuzhofen/snapdragon-ai-studio`

Para errores reproducibles, utiliza GitHub Issues. Para preguntas generales y debates, puede utilizarse GitHub Discussions si está habilitado para el repositorio.

No publiques credenciales, tokens u otra información confidencial en registros o capturas de pantalla incluidos en informes de errores.

---

## 21. Código abierto, licencias y marcas

Snapdragon AI Studio se desarrolla como un proyecto independiente de código abierto. La propia aplicación se distribuye bajo la licencia del proyecto indicada en el repositorio. Los modelos, frameworks y componentes externos están sujetos además a sus respectivas licencias y condiciones de uso.

Qualcomm, Snapdragon y Hexagon son marcas comerciales o marcas registradas de Qualcomm Incorporated. Windows es una marca de Microsoft. Las demás marcas pertenecen a sus respectivos propietarios.

El uso de estos nombres describe plataformas técnicas o compatibilidad y no implica una asociación oficial ni pertenencia a un producto.

---

## 22. RC2A de un vistazo

RC2A se centra especialmente en un flujo de usuario más fiable y comprensible:

- configuración inicial guiada,
- Gestor de modelos apto para principiantes,
- fuentes y descargas de modelos guiadas,
- activación automática después de una instalación correcta,
- indicadores de estado y progreso mejorados,
- Phoenix Boost con AI Boost local opcional,
- proceso automatizado de Qualcomm QAI AppBuilder para Stable Diffusion 3.5 Medium,
- generación local de imágenes en Windows 11 ARM64 / Snapdragon.

El objetivo sigue siendo deliberadamente sencillo:

> **Instalar Snapdragon AI Studio → seleccionar un modelo → generar una imagen.**

---

**Snapdragon AI Studio – Phoenix Engine**  
Holger Kreuzhofen  
Founder & Lead Developer
