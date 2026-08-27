# HK NPU STUDIO – Phoenix Engine
## Manual de usuario – Versión 2.0 RC2B

> **Proyecto independiente de código abierto para Windows en Snapdragon.**  
> HK NPU STUDIO no es un producto oficial de Qualcomm Technologies, Inc. y no está patrocinado ni respaldado por Qualcomm.

---

## 1. Bienvenido

HK NPU STUDIO es una aplicación de escritorio para la generación local de imágenes con IA en equipos Windows 11 ARM64 con procesadores Snapdragon. **Phoenix Engine** se encarga de la gestión de modelos, la preparación y la ejecución de las canalizaciones de IA compatibles.

RC2B pone especial énfasis en un flujo guiado: **Instalar → seleccionar un modelo → generar una imagen.** Los detalles técnicos deben permanecer en segundo plano tanto como sea posible durante el uso normal.

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

## 3. Instalar RC2B

1. Descarga el instalador ARM64 actual desde la versión oficial de HK NPU STUDIO en GitHub.
2. Ejecuta `HKNPUStudio-2.0.0-rc.2b-ARM64-Setup.exe`.
3. Sigue el asistente de instalación de Windows.
4. Inicia **HK NPU STUDIO** desde el menú Inicio o desde el acceso directo creado.

> **Windows SmartScreen:** Windows puede mostrar una advertencia para una versión que todavía no sea ampliamente reconocida o no tenga una firma comercial. Utiliza únicamente instaladores obtenidos desde el repositorio oficial del proyecto.

Para el uso normal del instalador publicado no es necesario instalar Python por separado.

---

## 4. Primer inicio

RC2B guía a los nuevos usuarios durante la configuración inicial de forma mucho más clara que los candidatos de versión anteriores.

La página de inicio muestra el estado actual de configuración. Si todavía no hay ningún modelo utilizable configurado, la aplicación te guía hasta el Gestor de modelos. Tras completar correctamente la configuración, se actualiza el estado de disponibilidad y puedes pasar directamente a la primera generación de imágenes.

### Flujo básico

1. Inicia HK NPU STUDIO.
2. Abre el Gestor de modelos.
3. Selecciona el modelo compatible que desees.
4. Inicia el proceso de instalación ofrecido.
5. Deja que la instalación y la validación terminen por completo.
6. Activa el modelo o espera a la activación automática.
7. Cambia a la generación de imágenes.

En el flujo guiado normal no necesitas seleccionar por separado componentes internos de ONNX, QNN o del modelo.

---

## 5. Gestor de modelos

El Gestor de modelos muestra los modelos conocidos por HK NPU STUDIO y su estado actual.

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

RC2B utiliza distintas fuentes y métodos de instalación según el modelo. El Gestor de modelos intenta ocultar estas diferencias y ofrecer un flujo guiado.

### Stable Diffusion 1.5

Stable Diffusion 1.5 es una opción compacta para iniciarse en la generación local de imágenes y resulta especialmente adecuada para flujos rápidos de 512×512. Con una variante NPU compatible, Phoenix se encarga de la validación y activación necesarias del paquete.

### Stable Diffusion 2.1

Stable Diffusion 2.1 también está disponible como vía de generación orientada a Snapdragon/Qualcomm. La instalación y activación se realizan mediante el Gestor de modelos según la fuente configurada para el modelo.

### Stable Diffusion 3.5 Medium

RC2B incluye un proceso de configuración mucho más automatizado para **Stable Diffusion 3.5 Medium mediante Qualcomm QAI AppBuilder**. Este flujo se describe por separado en el siguiente capítulo.

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
6. importar los archivos generados a HK NPU STUDIO,
7. crear el manifiesto y la información de validación,
8. validar la instalación,
9. activar el modelo a continuación.

Durante el proceso, la ventana de instalación muestra el paso actual y el progreso.

### Qualcomm QAI AppBuilder

Este método utiliza el proyecto oficial QAI AppBuilder de Qualcomm. Phoenix busca el archivo ZIP esperado en la carpeta Descargas. Si no se encuentra automáticamente, la aplicación puede pedirte que selecciones el archivo ZIP.

El archivo ZIP del usuario no se elimina durante el proceso normal de instalación.

### Descarga del modelo

Durante la configuración, el script de Qualcomm descarga los archivos necesarios de SD3.5. La descarga es actualmente de aproximadamente **3,24 GB**. La velocidad y duración dependen de la conexión a Internet, el dispositivo de almacenamiento y el estado del sistema.

No cierres HK NPU STUDIO durante este proceso y deja que la instalación termine por completo.

### Finalización

Después de la configuración, se validan los archivos del modelo y este queda disponible para HK NPU STUDIO. El flujo de usuario correcto de RC2B se ha probado como una cadena completa:

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

**Phoenix Boost** es una función de HK NPU STUDIO para mejorar o ampliar los prompts antes de generar una imagen.

Existen dos modos fundamentalmente distintos.

### Deterministic Boost

El boost determinista local funciona sin un modelo de lenguaje adicional. Amplía el prompt mediante reglas reproducibles y puede utilizarse directamente.

### AI Boost

El AI Boost opcional utiliza un modelo de lenguaje ejecutado localmente para mejorar el prompt de forma más inteligente.

RC2B utiliza:

- **Ollama** como servicio local de modelos
- **Qwen2.5 3B** como modelo de lenguaje local previsto

Si Ollama o Qwen todavía no están disponibles, Phoenix Boost guía al usuario por la configuración necesaria. La descarga del modelo puede tardar algún tiempo.

Tras una instalación correcta, este boost funciona localmente en el ordenador. El prompt original no necesita enviarse a un servicio externo de optimización de prompts en la nube.

### Vista previa de Boost y edición

Antes de la generación real de la imagen, Phoenix Boost proporciona una vista previa interactiva para revisar el prompt optimizado.

- **Vista previa compacta:** Una vista optimizada y que ahorra espacio presenta los prompts de manera estructurada.
- **Prompt original y optimizado uno al lado del otro:** Los prompts originales y mejorados se muestran uno al lado del otro en una vista de dos columnas.
- **Prompts negativos uno al lado del otro:** Los prompts negativos también se colocan uno al lado del otro.
- **Barra de acciones fija:** Los botones de acción existentes permanecen accesibles fuera del área de desplazamiento.
- **Scroll-Fallback (Alternativa de desplazamiento):** Si el texto es más largo que el espacio disponible, un área de desplazamiento sirve de fallback para que el contenido siga accesible.
- **Maximizable y restaurable:** La ventana de vista previa se puede maximizar y restaurar a su tamaño original.

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

HK NPU STUDIO ofrece vistas de imágenes e historial para revisar las imágenes generadas.

### Galería e historial

La galería ofrece una vista estructurada de todas las imágenes generadas localmente.

- **Búsqueda, ordenación, tamaño de miniatura y filtros:** Puedes buscar en la galería, ordenar las imágenes según los criterios disponibles, ajustar el tamaño de las miniaturas y aplicar filtros.
- **Abrir carpeta de salida:** Este botón abre en el Explorador de Windows la carpeta de salida configurada para el usuario actual. Si la carpeta no existe, la aplicación la crea de forma segura.
- **Vista previa al pasar el ratón (Hover):** El interruptor de Phoenix "Vista previa: Act./Desact." se encuentra junto a "Abrir carpeta de salida".
  - **Activada por defecto:** La vista previa al pasar el ratón está activada de forma predeterminada.
  - **Con Act.:** Al pasar el cursor sobre la miniatura de una imagen en la galería, se abre inmediatamente la vista previa de la imagen.
  - **Con Desact.:** Al pasar el cursor sobre una miniatura, no se abre ninguna vista previa.
  - **Desactivar:** Desactivar la función cierra cualquier vista previa que esté abierta.
  - **Guardado del estado:** El ajuste se guarda de forma permanente.
  - **Independencia:** La selección de imágenes, el doble clic para abrir y el menú contextual siguen funcionando independientemente de este ajuste.

### Comparación de imágenes y validación de metadatos

La herramienta integrada de comparación de imágenes te permite analizar dos imágenes una al lado de la otra.

- **Cargar imágenes:** Puedes cargar la imagen original y la imagen de salida una al lado de la otra en la vista de comparación.
- **Opciones de zoom:** Los niveles de zoom *Ajustar (Fit)*, *50 %*, *100 %* y *200 %* se configuran para la vista de comparación a través de la barra de herramientas compartida.
- **Desplazamiento (Panning):** Cuando las imágenes se amplían, la sección se puede desplazar manteniendo pulsado el botón izquierdo del ratón.
- **Interruptor síncrono:**
  - Con **Sincronizar: Activado**, las posiciones de desplazamiento normalizadas se transfieren a la otra imagen (posiciones de imagen sincronizadas).
  - Con **Sincronizar: Desactivado**, las posiciones de desplazamiento permanecen independientes.
- **Intercambiar:** Puedes intercambiar las posiciones de las dos imágenes cargadas.
- **Comparar metadatos de generación:** Puedes comparar directamente los parámetros de generación incrustados de ambas imágenes.
  - *Aclaración importante:* La comparación de metadatos es una comparación puramente de texto de los parámetros técnicos de generación. **No** es una comparación visual de píxeles y **no** se resalta en color ninguna área diferente de la imagen.
  - *Mensajes de estado:* La aplicación compara los metadatos con precisión y distingue claramente entre:
    - *Metadatos ausentes* (no se encontraron metadatos en ninguna de las imágenes),
    - *Metadatos unilaterales* (solo una de las imágenes contiene metadatos),
    - *Metadatos idénticos* (ambas imágenes se generaron con exactamente los mismos parámetros),
    - *Metadatos diferentes* (los parámetros difieren entre sí).

La presentación exacta puede seguir evolucionando entre candidatos de versión.

---

## 14. Idioma, temas y escalado de Windows

La interfaz de usuario admite:

- Alemán
- Inglés
- Español

### Opciones de tema (Claro y Oscuro)

Están disponibles un **Tema claro (Light)** y un **Tema oscuro (Dark)**. El idioma y el tema se pueden cambiar en cualquier momento en la configuración de la aplicación. La paridad de temas garantiza que todos los elementos de control sigan siendo visualmente atractivos y fáciles de leer con un alto contraste en ambas variantes de color.

### Escalado de Windows y responsividad

La interfaz de Phoenix está optimizada para el escalado de pantalla de Windows del **100 % al 175 %**.

- **Ajuste flexible (Wrapping):** Los elementos de control y las barras de acciones se adaptan dinámicamente al tamaño y al escalado de la ventana. El ajuste automático evita que se corten los botones.
- **Áreas de desplazamiento local:** Estas áreas mantienen accesibles el contenido y las acciones importantes con escalado alto o poca altura de ventana.

---

## 15. Datos y modelos locales

HK NPU STUDIO almacena localmente la configuración de la aplicación, los datos de trabajo y los modelos instalados.

Con una instalación normal mediante el instalador, los datos productivos de los modelos pueden encontrarse en el área local de la aplicación del usuario de Windows, por ejemplo:

```text
%LOCALAPPDATA%\HK NPU STUDIO\models
```

Las rutas internas pueden variar entre las versiones de desarrollo y las versiones instaladas. **No muevas ni elimines manualmente los archivos de modelos** salvo que estés realizando deliberadamente un diagnóstico.

La aplicación valida las instalaciones de modelos mediante los archivos y metadatos esperados. Una eliminación o un traslado manual incompleto puede hacer que el modelo se detecte como no válido.

---

## 16. Privacidad y funcionamiento sin conexión

Uno de los objetivos centrales de HK NPU STUDIO es la ejecución local de IA.

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

Reinicia HK NPU STUDIO y abre el Gestor de modelos. Según el modelo, Phoenix puede reutilizar datos completos existentes u ofrecer una nueva descarga.

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

- versión de HK NPU STUDIO
- versión de Windows
- dispositivo/procesador Snapdragon
- modelo utilizado
- pasos exactos hasta el error
- mensaje o captura de pantalla relevante
- archivos de registro correspondientes, si están disponibles

---

## 18. Desinstalación

HK NPU STUDIO puede desinstalarse desde **Configuración de Windows → Aplicaciones → Aplicaciones instaladas**.

Ten en cuenta que los archivos grandes de modelos y los datos del usuario pueden almacenarse por separado según la estrategia de instalación y almacenamiento. Antes de eliminar algo manualmente, comprueba si deseas conservar las imágenes generadas o los modelos.

---

## 19. Preguntas frecuentes

### ¿HK NPU STUDIO es un producto oficial de Qualcomm?

No. HK NPU STUDIO es un proyecto independiente de código abierto.

### ¿Se envían mis prompts a un servicio de imágenes en la nube?

La generación de imágenes compatible está diseñada para ejecutarse localmente. Sin embargo, se necesita una conexión a Internet para descargar y configurar algunos componentes.

### ¿Tengo que instalar Python?

No para el uso normal del instalador publicado para Windows. Python 3.11 ARM64 es relevante principalmente para el desarrollo o la ejecución desde el código fuente. La configuración de SD3.5 gestiona su proceso previsto mediante Phoenix.

### ¿Tengo que instalar Ollama?

Solo si quieres utilizar el **Phoenix AI Boost** opcional. La generación normal de imágenes debe funcionar sin Ollama.

### ¿Qué modelo de lenguaje utiliza Phoenix AI Boost?

RC2B utiliza **Qwen2.5 3B** mediante Ollama.

### ¿Tengo que recopilar manualmente archivos individuales de Qualcomm para SD3.5?

El flujo de RC2B está diseñado para automatizar la configuración de Qualcomm en la medida de lo posible. El usuario no debería tener que seleccionar manualmente componentes internos individuales del modelo.

### ¿Puedo eliminar los modelos directamente de sus carpetas?

No se recomienda durante el uso normal. Utiliza los procesos previstos de gestión e instalación. Los cambios manuales pueden hacer que el estado guardado y los archivos reales difieran temporalmente.

### ¿Qué idiomas admite la interfaz?

Alemán, inglés y español.

### ¿Puedo utilizar HK NPU STUDIO en equipos Intel o AMD?

El proyecto está diseñado para Windows 11 ARM64 en Snapdragon. Otras plataformas no forman parte del objetivo principal oficialmente previsto o validado.

---

## 20. Soporte e informes de errores

Repositorio del proyecto:

`https://github.com/Kreuzhofen/snapdragon-ai-studio`

Para errores reproducibles, utiliza GitHub Issues. Para preguntas generales y debates, puede utilizarse GitHub Discussions si está habilitado para el repositorio.

No publiques credenciales, tokens u otra información confidencial en registros o capturas de pantalla incluidos en informes de errores.

---

## 21. Código abierto, licencias y marcas

HK NPU STUDIO se desarrolla como un proyecto independiente de código abierto. La propia aplicación se distribuye bajo la licencia del proyecto indicada en el repositorio. Los modelos, frameworks y componentes externos están sujetos además a sus respectivas licencias y condiciones de uso.

Qualcomm, Snapdragon y Hexagon son marcas comerciales o marcas registradas de Qualcomm Incorporated. Windows es una marca de Microsoft. Las demás marcas pertenecen a sus respectivos propietarios.

El uso de estos nombres describe plataformas técnicas o compatibilidad y no implica una asociación oficial ni pertenencia a un producto.

---

## 22. RC2B de un vistazo

RC2B se centra en un flujo de usuario fiable y comprensible, junto con una interfaz modernizada:

- **Configuración inicial guiada:** Inicio estructurado para nuevos usuarios directamente desde el primer arranque.
- **Gestor de modelos apto para principiantes:** El inspector sigue siendo desplazable mientras la barra de instalación de modelos y sus acciones permanecen accesibles.
- **Fuentes y descargas de modelos guiadas:** Proceso automatizado de Qualcomm QAI AppBuilder para Stable Diffusion 3.5 Medium.
- **Activación automática:** Activación del modelo inmediatamente después de una instalación y validación correctas.
- **Indicadores de estado y progreso:** Comentarios claros durante la configuración y la generación.
- **Phoenix Boost con AI Boost opcional:** Expansión inteligente de prompts a través de Ollama/Qwen local con una vista previa compacta (maximizable/restaurable, prompts uno al lado del otro, barra de acciones fija y scroll-fallback).
- **Generación local de imágenes:** Tras la configuración necesaria, la generación se ejecuta localmente en Windows 11 ARM64/Snapdragon. La configuración y las descargas aún pueden requerir Internet.
- **Interfaz responsive:** Optimizada para el escalado de Windows del 100 % al 175 % con ajuste dinámico y áreas de desplazamiento local.
- **Carpeta de salida fiable:** Abre directamente la carpeta de salida configurada y la crea de forma segura si no existe.
- **Vista previa opcional al pasar el ratón en la galería:** Vista previa de la imagen al pasar el cursor sobre las miniaturas (interruptor junto a la carpeta de salida, el estado se guarda, al desactivar se cierra la vista previa activa).
- **Comparación de imágenes y sincronización:** Barra de herramientas compartida para zoom (Ajustar, 50 %, 100 %, 200 %), desplazamiento con el botón izquierdo del ratón y posiciones sincronizadas o independientes (Sincronizar: Act./Desact.).
- **Comparación de metadatos comprensible:** Comparación de texto de los parámetros con mensajes de estado claros (sin comparación visual de píxeles).

El objetivo sigue siendo deliberadamente sencillo:

> **Instalar HK NPU STUDIO → seleccionar un modelo → generar una imagen.**

---

**HK NPU STUDIO – Phoenix Engine**
Holger Kreuzhofen  
Founder & Lead Developer
