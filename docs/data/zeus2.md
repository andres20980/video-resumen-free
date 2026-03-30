Aquí tienes un resumen completo y detallado del video, siguiendo tus instrucciones:

## Resumen Ejecutivo
El video presenta una exploración exhaustiva de la plataforma "Zeus Classic" de Mapfre, una herramienta central para la gestión de productos, despliegues y tareas. El ponente, Ricardo, navega por sus funcionalidades, mostrando la creación de productos, la gestión de releases, la integración con herramientas como GitHub Actions, CMDB, Jira y AWS. También se aborda la nueva versión, "Zeus One Team", que se compara desfavorablemente con la Classic en términos de rendimiento y funcionalidad. Durante la demostración de Zeus One Team, se revela una discusión con Asier sobre los requisitos de Teo para integrar telemetría de QA y la ejecución de pruebas automáticas. El video concluye con una crítica a la falta de resiliencia y caché de Zeus Classic y los problemas de rendimiento de Zeus One Team, sugiriendo la necesidad de una intervención significativa para mejorar ambas plataformas.

## Información del Contenido
- **Tipo**: Demostración de plataforma / Revisión de herramientas internas
- **Tema principal**: Exploración y análisis de las plataformas "Zeus Classic" y "Zeus One Team" de Mapfre, sus funcionalidades, integraciones, problemas de rendimiento y requisitos de mejora, especialmente en el ámbito de QA.
- **Participantes**:
    - **Ricardo**: Ponente principal y demostrador.
    - **Alejandro Molina**: Mencionado como contacto asociado al producto Zeus.
    - **Álvaro**: Compañero que trabajó en la ejecución de planes de despliegue.
    - **Asier**: Interviene en la conversación para recordar los requisitos de Teo.
    - **Teo**: Mencionado como la persona que solicitó la inclusión de telemetría de QA y ejecución de pruebas en Zeus One Team a través de una RFP.
    - **Juan**: Mencionado por Ricardo al expresar su preferencia por Zeus Classic sobre One Team.
    - **Andrés**: Preguntado por Ricardo sobre el uso de Zeus en Maudi.
    - **Nini**: Mencionada por Ricardo como la persona con la que hablará sobre los problemas del front-end.
    - **Josemi**: Mencionado por Ricardo como alguien que fue "muy sincero" sobre el mal estado del back-end.
- **Tono**: Informativo, demostrativo, crítico (especialmente hacia el rendimiento y la usabilidad de las plataformas), y algo frustrado.

## Índice Temporal
- **0:00 - 1:05**: Introducción a Zeus Classic: Dashboard, listado de noticias, tareas y planes. Vista general de productos.
- **1:05 - 2:45**: Exploración de productos: Ejemplo "Plataforma de prestaciones no vida". Componentes de infraestructura y despliegue. Permisos limitados del usuario.
- **2:45 - 4:00**: Entornos y despliegue: Visualización de las tres cuentas de AWS (desarrollo, preproducción, producción). Confirmación de que Zeus funciona en AWS.
- **4:00 - 5:20**: Problemas de filtrado y búsqueda: Dificultad para ver todos los productos. Mención de "Observabilidad de la plataforma de ingeniería" y búsqueda de "Zeus chatbot" y "Soporte Zeus". Identificación de Alejandro Molina.
- **5:20 - 6:50**: Detalle de un producto: "Gestión de servicios de colaboradores". Descripción como BCF que expone servicios a una app móvil, dentro de la "Plataforma de prestaciones no vida". Componentes (BCF, API Gateway) y repositorio GitHub.
- **6:50 - 8:40**: Gestión de releases y despliegues: Configuración con GitHub Actions para lanzar releases. Proceso de generación de releases. Mención de Álvaro y la ejecución de planes de despliegue en INT, PRE y PRO. Zeus orquesta GitHub Actions.
- **8:40 - 10:05**: Integraciones y herramientas: Integración con Poseidón. Sección de FinOps (rota). Tareas ejecutadas, entornos lógicos y planes de despliegue.
- **10:05 - 12:00**: Herramientas y configuraciones: Acciones y workflows. Integración con CMDB (registro de proyectos, Service Manager de IBM, URL). Configuración de Jira. Ausencia de Bitbucket y herramientas DevOps.
- **12:00 - 13:25**: Problemas de rendimiento de Zeus Classic: Falta de resiliencia y caché. Consultas lentas (ej. GitHub). Límite de 29 segundos del API Gateway de AWS.
- **13:25 - 14:05**: APIs y gestión de usuarios: Exposición de APIs a través del marketplace de Mapfre, dashboard Swagger. Gestión de usuarios (asignación por ID de Mapfre, roles, permisos). Problemas de interfaz.
- **14:05 - 15:00**: Introducción a Zeus One Team: Nueva interfaz, chatbot, estructura de Mapfre, búsqueda por dominio/producto. Percepción de que el contenido es de pruebas.
- **15:00 - 16:45**: Zeus One Team y requisitos de QA: Exploración de productos (ej. Golden Record). Intervención de Asier y Ricardo sobre la RFP de Teo para incluir telemetría de QA (ejecuciones de pruebas, nivel de calidad, cobertura, defectos) y ejecución de rondas de pruebas automáticas en "servicios disponibles" y "CD y QA".
- **16:45 - 18:00**: Comparación y problemas de Zeus One Team: Ricardo prefiere Classic. Dificultad para encontrar proyectos activos. Problemas con la gestión de releases y entornos (no declarados, errores).
- **18:00 - 19:30**: Conclusión y próximos pasos: Problemas de rendimiento y funcionalidad en Zeus One Team (entornos no seleccionados, GitHub no enlazado). Frustración general. Necesidad de "fontaneros". Conversación con Andrés sobre el uso de Zeus en Maudi (posiblemente solo para Mapfre 2.0). Ricardo hablará con Nini sobre el front-end, Josemi ya criticó el back-end.

## Contenido Detallado

**Exploración de Zeus Classic (0:00 - 14:05)**
El video comienza con una demostración del portal **Zeus Classic**, mostrando un dashboard con listado de noticias, tareas y planes. Ricardo explica que todo se gestiona a través de "productos". Muestra un ejemplo de producto llamado "Plataforma de prestaciones no vida", que es la plataforma base donde se despliegan los proyectos. Esta plataforma tiene datos, componentes de infraestructura y despliegue, y no tiene un ciclo de vida de desarrollo propio, siendo más una parte de infraestructura.

Ricardo encuentra limitaciones de permisos para ver ciertas secciones como "parámetros globales". Sin embargo, en la sección de Poseidón, puede ver los entornos, confirmando que Zeus opera en **AWS** con tres cuentas: desarrollo, preproducción y producción. Se menciona que Zeus se despliega en la plataforma de integración o ingeniería.

La navegación por la lista de productos es lenta y presenta problemas de filtrado, lo que Ricardo describe como "un peñazo". Se encuentra el producto "Zeus" y se menciona a **Alejandro Molina** como uno de los contactos.

Se profundiza en un producto específico: "Gestión de servicios de colaboradores", un BCF (Business Component Framework) que expone servicios a una aplicación móvil. Este producto está anidado dentro de la "Plataforma de prestaciones no vida". Tiene dos componentes: un BCF y un API Gateway. El repositorio de código está en **GitHub**, y las releases se gestionan mediante **GitHub Actions**. Ricardo explica el proceso de generar una nueva release a partir de un tag o rama. Se menciona a **Álvaro** como el compañero que ha ejecutado planes de despliegue en entornos INT (integración), PRE (preproducción) y PRO (producción). Zeus orquesta los pipelines de despliegue que residen en GitHub Actions.

Zeus Classic se integra con otras herramientas como **Poseidón** (donde se ven los entornos de la plataforma de prestaciones, pero no de productos de bajo nivel) y tiene una sección de **FinOps** que, en el momento de la demostración, está "rota". También muestra tareas ejecutadas, entornos lógicos y ventanas de despliegue.

En la sección de "Tools", se detallan las integraciones:
- **CMDB**: Los proyectos deben registrarse aquí. Se debe abrir una petición en el **Service Manager de IBM** y luego registrar la URL en Zeus para activarlo.
- **Jira**: Se configuran las URLs del Jira del proyecto.
- **Bitbucket**: No está configurado para este proyecto.
- **DevOps tools**: Se asume que no hay nada configurado.

Ricardo critica la falta de resiliencia y caché de Zeus Classic, lo que provoca lentitud en las consultas (ej. a GitHub). Destaca que el **API Gateway de AWS** tiene un límite de **29 segundos**, y si una consulta excede este tiempo, da error.

Finalmente, en Zeus Classic, se mencionan las APIs expuestas a través del **marketplace de Mapfre** y un dashboard que pintaría el **Swagger** de las APIs. La gestión de usuarios permite asignar nuevos usuarios por su identificador de Mapfre y asignar roles, aunque la interfaz presenta problemas visuales.

**Exploración de Zeus One Team (14:05 - 19:30)**
Ricardo pasa a **Zeus One Team**, una nueva interfaz que, según su opinión, ha "empeorado" respecto a Classic. Muestra un asistente/chatbot y la estructura de Mapfre, permitiendo buscar por dominio o producto. Ricardo no está asignado a ningún dominio y sospecha que gran parte del contenido es de pruebas.

Al explorar los productos en One Team, se menciona el "Golden Record" como un proyecto de prueba. En este punto, **Asier** interrumpe a Ricardo para recordar los requisitos de **Teo** de una RFP (Request for Proposal). Teo desea incluir en la parte superior derecha de Zeus One Team (específicamente en "servicios disponibles") los enlaces para visualizar la **telemetría de QA**, incluyendo el estado del nivel de calidad, cobertura y defectos (ej. categoría A). También se quiere integrar la posibilidad de ejecutar rondas de pruebas automáticas desde la sección "CD y QA".

Ricardo continúa explorando One Team, notando que el rendimiento es aún peor que el de Classic. Intenta encontrar proyectos activos, pero solo encuentra proyectos antiguos o de prueba. Se frustra al ver que los entornos no están declarados o no funcionan correctamente ("entorno no seleccionado") y que GitHub no está enlazado.

**Conclusiones y Próximos Pasos (19:00 - 19:30)**
Ricardo expresa su gran frustración con el estado de Zeus One Team, sugiriendo que el equipo es requerido como "fontaneros" para solucionar los problemas. Pregunta a **Andrés** si usaron Zeus en Maudi, a lo que Andrés responde que no, usando directamente Jenkins. Ricardo especula que Zeus podría ser solo para productos de Mapfre 2.0. Concluye que hablará con **Nini** sobre los problemas del front-end, recordando que **Josemi** ya había sido "muy sincero" sobre el mal estado del back-end.

## Puntos Clave y Conclusiones
1.  **Zeus Classic es una plataforma central en Mapfre** para la gestión de productos, despliegues y tareas, con integraciones con AWS, GitHub Actions, CMDB y Jira.
2.  **Zeus opera en AWS**, utilizando cuentas separadas para desarrollo, preproducción y producción.
3.  **La gestión de releases se orquesta a través de Zeus, pero los pipelines de despliegue residen en GitHub Actions.**
4.  **Zeus Classic sufre de problemas de rendimiento**, atribuidos a la falta de resiliencia y caché, y es susceptible a los timeouts de 29 segundos del API Gateway de AWS.
5.  **Zeus One Team es una nueva interfaz que se percibe como inferior a Classic** en términos de rendimiento y funcionalidad, con problemas significativos en la visualización de entornos y enlaces a repositorios.
6.  **Existe un requisito explícito (RFP de Teo) para integrar la telemetría de QA** (estado de calidad, cobertura, defectos) y la capacidad de ejecutar pruebas automáticas en Zeus One Team.
7.  **Hay una clara necesidad de mejora en ambas plataformas**, tanto en el front-end (según Ricardo y Nini) como en el back-end (según Josemi).
8.  **El equipo de Ricardo se ve a sí mismo como "fontaneros"** encargados de solucionar los problemas existentes en la plataforma.

## Decisiones y Próximos Pasos
- **Integrar Telemetría de QA en Zeus One Team**: Se acordó, a raíz de la RFP de Teo y la discusión con Asier, que se debe incluir la visualización del estado de calidad, cobertura de pruebas y defectos en la sección de "servicios disponibles" de Zeus One Team.
- **Implementar Ejecución de Pruebas Automáticas**: Se debe añadir la funcionalidad para lanzar rondas de pruebas automáticas desde la sección "CD y QA" de Zeus One Team.
- **Desarrollar Dashboards de Información Telemétrica**: Se requiere la creación de dashboards para visualizar la información telemétrica de QA.
- **Ricardo hablará con Nini**: Para abordar y discutir los problemas y deficiencias observadas en el front-end de la plataforma.
- **Intervención del equipo**: El equipo de Ricardo se prepara para actuar como "fontaneros" para solucionar los problemas de la plataforma.

## Notas Adicionales
- **Tecnologías y Herramientas Mencionadas**: Zeus Classic, Zeus One Team, AWS (cuentas de desarrollo, preproducción, producción), API Gateway (límite de 29 segundos), GitHub, GitHub Actions, Poseidón, CMDB, IBM Service Manager, Jira, Bitbucket (no usado), Swagger, Jenkins (usado en Maudi).
- **Conceptos**: BCF (Business Component Framework), RFP (Request for Proposal), Telemetría de QA, FinOps.
- **Problemas recurrentes**: Lentitud, falta de resiliencia y caché, problemas de interfaz de usuario, permisos limitados, dificultad de filtrado, secciones rotas (FinOps), entornos no funcionales.
- **Mapfre 2.0**: Se sugiere que Zeus podría estar destinado específicamente para productos de esta iniciativa.