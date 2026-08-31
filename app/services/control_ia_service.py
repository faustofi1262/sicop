import os
from openai import OpenAI
from app.database import get_connection
CRITERIOS_DOCUMENTO = {

    "ESTUDIOS_PREVIOS": """
Analiza el documento como ESTUDIOS PREVIOS de un procedimiento
de contratación pública.

Revisa especialmente:
- justificación de la contratación;
- antecedentes;
- objetivo;
- alcance;
- coherencia entre necesidad y contratación;
- información técnica utilizada;
- identificación de riesgos o inconsistencias;
- coherencia con el objeto de contratación;
- posibles direccionamientos;
- información que pudiera afectar la competencia;
- ausencia de información necesaria para continuar el procedimiento.
""",

    "DETERMINACION_NECESIDAD": """
Analiza el documento como DETERMINACIÓN DE LA NECESIDAD.

Debes revisar OBLIGATORIAMENTE todos los siguientes componentes.

1. IDENTIFICACIÓN DE LA NECESIDAD
- Verificar que se explique claramente cuál es la necesidad institucional
  que se pretende atender.
- Diferenciar la necesidad institucional de la simple intención de
  adquirir un bien o contratar un servicio.
- Identificar textos genéricos que no permitan comprender el problema,
  requerimiento o necesidad que origina la contratación.
- No inventar necesidades que no consten en el documento.

2. ANTECEDENTES Y JUSTIFICACIÓN
- Verificar que los antecedentes permitan comprender el origen de la
  contratación.
- Verificar que la justificación explique razonablemente por qué la
  contratación resulta necesaria.
- Identificar contradicciones entre antecedentes, necesidad,
  justificación y objeto.
- No generar observaciones por falta de información histórica que no
  sea necesaria para justificar la contratación.

3. COMPETENCIA Y FINALIDAD INSTITUCIONAL
- Verificar que la necesidad guarde relación con las actividades,
  funciones, competencias o finalidad institucional descritas en el
  propio documento.
- No inventar competencias institucionales que no estén disponibles
  en la información proporcionada.
- Cuando no exista información suficiente para comprobar este punto,
  indicar únicamente que requiere verificación documental.

4. OBJETO DE CONTRATACIÓN
- Verificar que el objeto responda directamente a la necesidad
  identificada.
- Verificar que sea coherente con la justificación y alcance.
- Identificar componentes incluidos en el objeto que no hayan sido
  sustentados previamente.
- Identificar necesidades descritas que posteriormente no sean
  atendidas por el objeto propuesto.

5. BENEFICIO
- Identificar cuál es el beneficio esperado para la institución,
  usuarios o destinatarios de la contratación.
- Verificar que el beneficio tenga relación directa con la necesidad.
- No aceptar como análisis suficiente afirmaciones genéricas como
  "beneficiará a la institución" cuando no expliquen concretamente
  el resultado esperado.

6. EFICIENCIA
- Verificar si el documento explica razonablemente el uso de recursos
  para atender la necesidad.
- Analizar si se consideran cantidades, alcance, tiempo, condiciones
  de ejecución u otros elementos que permitan valorar la eficiencia
  de la contratación.
- No exigir cálculos económicos que no correspondan a la naturaleza
  de la contratación.

7. EFECTIVIDAD
- Verificar si la solución propuesta permite atender realmente la
  necesidad identificada.
- Comprobar coherencia entre necesidad, solución propuesta, alcance
  y resultado esperado.
- Identificar cuando la solución propuesta atienda solo parcialmente
  la necesidad sin que exista explicación suficiente.

8. MEJOR VALOR POR DINERO
- Verificar que el análisis no se limite exclusivamente al menor
  precio cuando la naturaleza de la contratación requiera considerar
  otros factores relevantes.

- Revisar, cuando corresponda, factores tales como:
  * calidad;
  * características técnicas;
  * desempeño;
  * plazo;
  * garantía;
  * mantenimiento;
  * costos asociados;
  * vida útil;
  * riesgos;
  * condiciones de ejecución;
  * resultados esperados.

- Los factores anteriores son referenciales.
  NO exigir todos ellos en cada contratación.

- Determinar cuáles resultan pertinentes según el objeto y naturaleza
  de la contratación.

- Verificar que exista una explicación razonable de por qué la
  alternativa propuesta representa una utilización adecuada de los
  recursos públicos.

- No inventar alternativas que la unidad requirente no haya analizado.

9. CICLO DE VIDA
- Cuando por la naturaleza del bien, obra o servicio corresponda,
  verificar si se consideran costos o condiciones posteriores a la
  adquisición.

- Pueden comprender, cuando sean aplicables:
  * operación;
  * mantenimiento;
  * consumibles;
  * repuestos;
  * soporte;
  * garantías;
  * vida útil;
  * disposición final.

- NO observar la ausencia de análisis de ciclo de vida cuando este no
  resulte material para la contratación.

10. PLANIFICACIÓN
- Verificar las referencias a planificación institucional, POA, PAC
  u otros instrumentos únicamente cuando consten en el documento.
- Identificar contradicciones concretas entre la información
  disponible.
- No afirmar que una contratación consta o no consta en instrumentos
  de planificación si estos no están disponibles para la revisión.

11. CANTIDADES Y DIMENSIONAMIENTO
- Cuando el documento incluya cantidades, número de beneficiarios,
  períodos, frecuencias u otras magnitudes, verificar que exista
  coherencia con la necesidad planteada.
- Comprobar cálculos cuando exista información suficiente.
- Identificar cantidades que no estén justificadas cuando puedan
  afectar materialmente el alcance o presupuesto.

12. PRESUPUESTO
- Verificar que el valor mencionado en la determinación de necesidad
  sea coherente internamente cuando exista.
- Comprobar operaciones matemáticas cuando el documento contenga
  información suficiente.
- No realizar conclusiones sobre la correcta determinación del
  presupuesto referencial cuando para ello sea necesario revisar
  otro documento que no forme parte del análisis actual.
- En ese caso indicar que corresponde realizar la comparación
  documental posteriormente.

13. PLAZO
- Cuando se establezca un plazo, verificar que sea coherente con la
  necesidad y la solución propuesta.
- Identificar contradicciones entre diferentes plazos o hitos de
  inicio contenidos en el mismo documento.
- No determinar por cuenta propia cuál debería ser el plazo correcto.

14. FORMA DE PAGO
- Cuando conste una forma de pago, verificar que sea coherente con
  la naturaleza de la contratación.
- Identificar contradicciones con entregas, productos, ejecución,
  anticipo o plazo cuando puedan comprobarse dentro del documento.
- No diseñar una nueva forma de pago por cuenta de la unidad
  requirente.

15. RIESGOS E INCONSISTENCIAS
- Identificar únicamente riesgos concretos derivados del contenido
  del documento.
- Priorizar contradicciones, información insuficiente, cálculos
  incorrectos, falta de justificación material o incoherencia entre
  necesidad y solución.
- No generar riesgos hipotéticos sin sustento documental.

REGLA FINAL:

Debes revisar todos los componentes anteriores, pero solamente generar
hallazgos cuando exista una situación concreta que requiera corrección,
aclaración o verificación.

No conviertas cada componente en un hallazgo.

Agrupa en un mismo hallazgo los problemas que tengan una causa común.

No repitas una observación de Mejor Valor por Dinero nuevamente como
beneficio, eficiencia, efectividad o ciclo de vida cuando corresponda
al mismo problema.

No inventes normativa ni artículos.
Cuando una conclusión dependa de información externa o de otro
documento que todavía no haya sido revisado, indica expresamente que
requiere verificación o comparación documental.
""",

    "ESPECIFICACIONES_TECNICAS": """
Analiza el documento como ESPECIFICACIONES TÉCNICAS.

Debes revisar OBLIGATORIAMENTE todos los siguientes componentes,
considerando la naturaleza concreta de los bienes objeto de contratación.

1. OBJETO Y COHERENCIA GENERAL
- Verificar que las especificaciones correspondan al objeto de
  contratación.
- Verificar que las características solicitadas permitan identificar
  claramente qué bien necesita la entidad.
- Identificar contradicciones entre objeto, descripción, cantidades
  y características técnicas.
- No inventar características que la unidad requirente no haya
  establecido.

2. DESCRIPCIÓN TÉCNICA
- Verificar que cada bien tenga una descripción suficientemente clara
  para permitir la preparación y comparación de ofertas.
- Identificar características ambiguas, contradictorias o imposibles
  de verificar.
- Verificar coherencia entre dimensiones, capacidades, materiales,
  rendimiento, características funcionales y demás parámetros cuando
  estos consten.
- No observar la ausencia de una característica solamente porque
  podría ser útil; debe ser necesaria para definir adecuadamente
  el bien.

3. MARCAS, MODELOS Y POSIBLE DIRECCIONAMIENTO
- Revisar si las especificaciones contienen marcas, fabricantes,
  modelos, códigos comerciales, referencias particulares u otros
  elementos que puedan identificar un producto determinado.
- Cuando exista una marca o modelo, indicar exactamente dónde aparece
  y analizar si corresponde realizar una verificación normativa.
- No afirmar automáticamente que existe direccionamiento únicamente
  por encontrar una referencia comercial.
- Identificar combinaciones de características excesivamente
  particulares cuando razonablemente puedan limitar la participación,
  pero explicar concretamente qué características generan el riesgo.
- No inventar marcas o modelos alternativos.

4. UNIDADES DE MEDIDA
- Verificar que la unidad de medida utilizada sea coherente con la
  descripción y naturaleza del bien.
- Comprobar que cantidades y unidades permitan determinar claramente
  qué debe entregarse.
- Identificar casos como unidad, paquete, caja, metro, kilogramo,
  litro, juego u otras unidades cuando exista contradicción con la
  descripción.
- No cambiar por cuenta propia la unidad de medida; indicar la
  inconsistencia para que sea corregida o aclarada.

5. CANTIDADES
- Verificar coherencia entre cantidades, descripción, presentación
  y unidad de medida.
- Cuando existan operaciones matemáticas, comprobarlas si existe
  información suficiente.
- Identificar cantidades contradictorias dentro del mismo documento.
- No determinar por cuenta propia la cantidad que debería adquirir
  la entidad.

6. NORMAS Y REQUISITOS TÉCNICOS
- Cuando se exijan normas técnicas, certificaciones, fichas,
  registros u otros requisitos técnicos, verificar que estén
  claramente identificados.
- Analizar su relación con la naturaleza del bien.
- Identificar requisitos cuya aplicación resulte contradictoria o
  no pueda verificarse con la información disponible.
- No inventar normas técnicas que no consten en el documento.

7. CONDICIONES DE ENTREGA
- Verificar que se determine, cuando corresponda:
  * lugar de entrega;
  * condiciones de entrega;
  * plazo;
  * recepción;
  * instalación, puesta en funcionamiento o pruebas cuando sean
    necesarias por la naturaleza del bien.
- Verificar coherencia entre estas condiciones.
- No exigir instalación, pruebas o puesta en funcionamiento para
  bienes cuya naturaleza no lo requiera.

8. PLAZO
- Verificar que el plazo esté claramente determinado.
- Verificar el hito desde el cual comienza a computarse cuando conste.
- Identificar diferentes plazos o hitos de inicio contradictorios.
- No establecer por cuenta propia cuál debería ser el plazo correcto.

9. FORMA DE PAGO
- Identificar si corresponde pago contra entrega, anticipo, pagos
  parciales u otra modalidad.
- Verificar que la forma de pago sea coherente con la entrega,
  recepción, instalación o cumplimiento de las obligaciones.
- Cuando exista anticipo, identificar su porcentaje y las condiciones
  establecidas, sin inventar requisitos adicionales.
- Cuando el pago sea contra entrega, verificar que pueda determinarse
  objetivamente qué condición o recepción habilita el pago.
- No diseñar una nueva forma de pago.

10. GARANTÍAS
- Identificar qué tipo de garantía se solicita.

- Cuando exista GARANTÍA TÉCNICA, verificar que se determine de forma
  suficientemente clara:
  * duración;
  * alcance;
  * condiciones de aplicación;
  * cobertura frente a defectos cuando corresponda;
  * mecanismo de atención, reparación o sustitución cuando esté
    previsto.

- Si el documento menciona una garantía técnica sin determinar
  elementos necesarios para conocer su alcance, generar la
  observación correspondiente.

- No determinar por cuenta propia cuántos años debe durar una garantía.

- No exigir garantía técnica cuando por la naturaleza del bien no
  corresponda.

11. OBLIGACIONES DEL CONTRATISTA
- Verificar que las obligaciones tengan relación directa con la
  entrega y cumplimiento del objeto.
- Identificar obligaciones excesivas, innecesarias, contradictorias
  o ajenas a la contratación.
- Diferenciar requisitos exigibles al oferente de obligaciones
  correspondientes al contratista durante la ejecución.
- No crear nuevas obligaciones por cuenta de la unidad requirente.

12. PERSONAL TÉCNICO
- Si se exige personal técnico, verificar primero que guarde relación
  con la naturaleza y complejidad de la contratación.
- Verificar que se identifique claramente qué personal se requiere.
- Cuando se exija formación, experiencia u otras condiciones,
  verificar que estén claramente determinadas.
- Verificar que existan medios objetivos de acreditación.
- Identificar requisitos desproporcionados cuando exista sustento
  concreto para hacerlo.
- No observar la ausencia de personal técnico cuando la contratación
  no lo requiera.

13. EQUIPO MÍNIMO
- Si se exige equipo mínimo para ejecutar la contratación, verificar
  que los equipos estén claramente identificados.
- Verificar que tengan relación con la entrega, instalación,
  configuración u otras actividades requeridas.
- Verificar que existan medios objetivos para acreditar su
  disponibilidad cuando corresponda.
- No observar la ausencia de equipo mínimo cuando la contratación
  no lo requiera.

14. EXPERIENCIA
- Si se exige experiencia al oferente, verificar que esté claramente
  determinada y tenga relación con el objeto de contratación.
- Verificar que existan medios objetivos para acreditarla.
- Analizar su proporcionalidad cuando exista información suficiente.
- No exigir experiencia automáticamente por tratarse de una
  contratación pública.

15. ÍNFIMA CUANTÍA HASTA USD 10.000

- Cuando el presupuesto referencial sea HASTA USD 10.000 y corresponda
  a ÍNFIMA CUANTÍA, la evaluación deberá estructurarse como
  CUMPLE / NO CUMPLE.

- NO exigir metodología de evaluación por puntaje.

- Si se exige experiencia, personal técnico, equipo mínimo,
  garantías u otros requisitos:
  * verificar que sean necesarios y proporcionales al objeto;
  * verificar que estén claramente definidos;
  * verificar que existan medios objetivos de acreditación;
  * verificar que puedan calificarse como CUMPLE / NO CUMPLE.

- NO recomendar puntajes para experiencia, personal técnico,
  equipo mínimo u otros requisitos.

- NO exigir estos requisitos únicamente por tratarse de una
  contratación pública.

16. CONTRATACIONES SUPERIORES A USD 10.000

- Identificar OBLIGATORIAMENTE el tipo de procedimiento antes de
  analizar la metodología de evaluación.

A. SUBASTA INVERSA ELECTRÓNICA

- Cuando el procedimiento corresponda a SUBASTA INVERSA ELECTRÓNICA,
  la revisión de los requisitos técnicos se realizará bajo
  CUMPLE / NO CUMPLE.

- NO exigir metodología de evaluación por puntaje.

- Verificar como CUMPLE / NO CUMPLE, cuando hayan sido requeridos:
  * especificaciones técnicas;
  * experiencia;
  * personal técnico;
  * equipo mínimo;
  * garantías;
  * condiciones de entrega;
  * plazo;
  * documentación y medios de acreditación.

- Verificar que estos requisitos sean objetivos, verificables,
  proporcionales y relacionados con el objeto de contratación.

- NO recomendar otorgar puntaje por experiencia, personal técnico,
  equipo mínimo u otros requisitos dentro de la Subasta Inversa
  Electrónica.

B. LICITACIÓN DE BIENES

- Cuando el procedimiento corresponda a LICITACIÓN DE BIENES,
  diferenciar claramente:

  1. requisitos mínimos evaluados como CUMPLE / NO CUMPLE; y

  2. parámetros que correspondan a EVALUACIÓN POR PUNTAJE.

- Verificar que los requisitos mínimos permitan determinar
  objetivamente si la oferta CUMPLE o NO CUMPLE.

- Cuando corresponda evaluación por puntaje, verificar que los
  parámetros puntuables sean coherentes con el modelo de pliego
  aplicable.

- Verificar que cada parámetro puntuable:
  * esté claramente definido;
  * sea objetivo;
  * sea medible;
  * tenga una escala o fórmula aplicable;
  * establezca su puntaje máximo;
  * determine el medio de acreditación correspondiente.

- Identificar contradicciones entre un requisito mínimo
  CUMPLE / NO CUMPLE y el mismo requisito utilizado posteriormente
  para asignar puntaje.

- NO inventar parámetros de evaluación que no correspondan al
  procedimiento o al modelo aplicable.

C. OTROS PROCEDIMIENTOS

- Si el procedimiento no corresponde a ÍNFIMA CUANTÍA,
  SUBASTA INVERSA ELECTRÓNICA o LICITACIÓN DE BIENES,
  identificar primero el procedimiento aplicable.

- No asumir automáticamente que corresponde evaluación por puntaje.

- Determinar si el procedimiento contempla:
  * únicamente CUMPLE / NO CUMPLE; o
  * CUMPLE / NO CUMPLE más evaluación por puntaje.

- Aplicar la revisión conforme al procedimiento identificado.

17. REQUISITOS RESTRICTIVOS
- Identificar únicamente requisitos que puedan resultar restrictivos
  cuando exista una razón concreta y explicable.
- Analizar especialmente combinaciones innecesarias de características,
  certificaciones, experiencia, personal, equipos, marcas o condiciones
  que puedan reducir injustificadamente la participación.
- No considerar restrictivo un requisito únicamente porque sea
  exigente.
- Explicar qué requisito genera el riesgo y por qué.

18. COHERENCIA INTERNA
- Comparar entre sí las diferentes secciones de las especificaciones.
- Identificar contradicciones en:
  * cantidades;
  * características;
  * unidades;
  * plazo;
  * garantías;
  * entrega;
  * pago;
  * obligaciones;
  * personal;
  * equipos;
  * experiencia.
- Consolidar contradicciones relacionadas en un mismo hallazgo.

REGLA FINAL:

Debes revisar TODOS los componentes anteriores aunque algunos no
generen observaciones.

NO conviertas cada componente en un hallazgo.

No inventes requisitos técnicos que la unidad requirente debería
incorporar.

La función de la revisión es identificar qué debe corregirse,
aclararse, completarse o verificarse; NO diseñar las especificaciones
técnicas por cuenta de la unidad requirente.

Cuando varios problemas estén relacionados, consolídalos en un mismo
hallazgo.

No inventes normativa ni números de artículos.

Cuando una conclusión dependa de una regla normativa que no esté
disponible en el contexto de la revisión, indica que requiere
verificación normativa.
""",

    "TERMINOS_REFERENCIA": """
Analiza el documento como TÉRMINOS DE REFERENCIA.

Debes revisar OBLIGATORIAMENTE todos los siguientes componentes.
La revisión debe determinar si cada componente es coherente con
el objeto y con la naturaleza del servicio contratado.

1. ANTECEDENTES
- Verificar que expliquen el origen y contexto de la contratación.
- Verificar que guarden relación directa con el objeto contractual.
- Observar únicamente contradicciones, información irrelevante o
  vacíos que afecten la comprensión de la contratación.

2. OBJETIVOS
- Verificar que el objetivo general sea coherente con el objeto.
- Si existen objetivos específicos, verificar que contribuyan al
  cumplimiento del objetivo general y de la contratación.
- Identificar contradicciones concretas.

3. ALCANCE
- Verificar que permita determinar claramente qué comprende el servicio.
- Verificar coherencia con el objeto, objetivos y actividades.
- Identificar exclusiones, ampliaciones o condiciones que contradigan
  el objeto de contratación.

4. METODOLOGÍA
- Verificar que describa concretamente cómo se ejecutará el servicio.
- Verificar actividades, procedimientos, coordinación, mecanismos de
  ejecución y responsabilidades cuando correspondan.
- No considerar suficiente una metodología que únicamente describa
  el procedimiento administrativo de contratación y no la forma en
  que se ejecutará el servicio.
- No exigir componentes metodológicos que no sean necesarios por la
  naturaleza del servicio.

5. INFORMACIÓN DISPONIBLE
- Verificar si para ejecutar el servicio es necesaria información,
  documentación, bases de datos, estudios u otros insumos que deban
  ser proporcionados por la entidad.
- Cuando sean necesarios, verificar que se encuentren identificados.
- No observar su ausencia cuando por la naturaleza del servicio no
  se requiera información institucional previa.

6. PRODUCTOS O SERVICIOS ESPERADOS
- Verificar que los productos, entregables o servicios esperados estén
  claramente identificados.
- Verificar coherencia con el objeto, alcance, metodología y plazo.
- Verificar que permitan determinar objetivamente cuándo el servicio
  ha sido ejecutado y puede ser recibido.
- Si existen entregables, verificar que sean identificables y
  verificables.
- Verificar su relación con la forma de pago cuando corresponda.

7. PLAZO
- Verificar que se establezca claramente la duración.
- Verificar el hito desde el cual comienza a computarse.
- Comprobar que no existan diferentes hitos de inicio o plazos
  contradictorios dentro del documento.

8. FORMA DE PAGO
- Identificar si corresponde pago contra entrega, anticipo, pagos
  parciales, periódicos u otra modalidad.
- Verificar coherencia entre la forma de pago y la ejecución del
  servicio.
- Cuando el pago dependa de productos, entregables o informes,
  verificar que estos se encuentren claramente determinados.
- Identificar contradicciones entre forma de pago, plazo y recepción.

9. OBLIGACIONES DEL CONTRATISTA
- Verificar que correspondan directamente al objeto y ejecución.
- Identificar obligaciones excesivas, innecesarias, contradictorias
  o ajenas al objeto.
- Diferenciar requisitos exigibles al oferente de obligaciones que
  corresponden al contratista durante la ejecución.

10. PERSONAL TÉCNICO
- Si se exige personal técnico, verificar que se identifiquen los
  perfiles requeridos.
- Verificar formación, experiencia u otros requisitos cuando sean
  exigidos.
- Verificar que existan medios claros de acreditación.
- No observar la ausencia de personal técnico cuando por la naturaleza
  del servicio no resulte necesario.

11. EQUIPO MÍNIMO
- Si se exige equipo, verificar que esté claramente identificado.
- Verificar que guarde relación con la ejecución del servicio.
- Verificar los medios establecidos para acreditar su disponibilidad.
- No observar la ausencia de equipos cuando no sean necesarios para
  ejecutar el objeto contractual.

12. EXPERIENCIA GENERAL Y ESPECÍFICA
- Identificar el presupuesto referencial.
- Identificar los montos o porcentajes exigidos para experiencia
  general y específica.
- Verificar los valores establecidos de acuerdo con la tabla aplicable
  del artículo 106 del Reglamento.
- Cuando existan datos suficientes, realizar el cálculo y comparar el
  resultado con lo establecido en el documento.
- Si existe diferencia, mostrar concretamente el valor establecido y
  el valor que resulte de la comprobación.
- Verificar los medios de acreditación exigidos.

13. METODOLOGÍA DE EVALUACIÓN
- Primero identificar el tipo de procedimiento de contratación.
- Determinar si corresponde evaluación por puntaje.
- Cuando corresponda, verificar que la metodología sea coherente con
  el modelo de pliego aplicable al tipo de procedimiento: licitación
  de obras, bienes, servicios, seguros o concurso público, según
  corresponda.
- Verificar que los parámetros puntuables sean objetivos, medibles y
  verificables.
- Verificar que se establezcan los medios de acreditación de cada
  parámetro puntuable.
- Verificar que las fórmulas y escalas de puntuación puedan aplicarse
  objetivamente.
- Identificar contradicciones entre requisitos mínimos de
  Cumple/No Cumple y parámetros posteriormente puntuables.

14. REQUISITOS RESTRICTIVOS O INNECESARIOS
- Identificar únicamente requisitos cuya falta de relación,
  desproporción o efecto restrictivo pueda sustentarse en el contenido
  del documento.
- No calificar automáticamente como restrictivo un requisito solamente
  por ser exigente.
- Explicar concretamente por qué el requisito podría afectar la
  participación o competencia.

REGLA FINAL:
Debes revisar los 14 componentes anteriores aunque algunos no generen
hallazgos.

No debes generar una observación simplemente porque un componente no
aparezca cuando este no sea necesario por la naturaleza de la
contratación.

Consolida en un mismo hallazgo las inconsistencias que tengan una
misma causa o estén directamente relacionadas.
""",

    "PRESUPUESTO_REFERENCIAL": """
Analiza el documento como DETERMINACIÓN DEL PRESUPUESTO REFERENCIAL.

Debes revisar obligatoriamente los siguientes componentes:

1. IDENTIFICACIÓN DEL PRESUPUESTO
- Identificar el valor del presupuesto referencial.
- Verificar que el valor sea claro y que exista coherencia entre
  subtotales, impuestos y valor total cuando estos consten.
- Comprobar matemáticamente los cálculos cuando exista información
  suficiente para hacerlo.

2. DETERMINACIÓN DEL RANGO
- Determinar si el presupuesto referencial es:
  * HASTA USD 10.000; o
  * SUPERIOR A USD 10.000.

- Esta clasificación debe realizarse antes de analizar la metodología
  utilizada para determinar el presupuesto.

3. CONTRATACIONES HASTA USD 10.000
- Cuando corresponda a ÍNFIMA CUANTÍA, revisar la determinación del
  presupuesto conforme a las reglas aplicables a este procedimiento.

- Verificar las proformas o fuentes utilizadas para establecer
  el valor de la contratación.

- Verificar que las proformas correspondan al mismo objeto o a
  prestaciones suficientemente comparables.

- Comparar:
  * descripción;
  * cantidades;
  * unidades de medida;
  * precios unitarios;
  * precios totales;
  * impuestos;
  * condiciones económicas relevantes.

- No exigir metodologías, estudios o estructuras propias de otros
  procedimientos cuando no correspondan a ÍNFIMA CUANTÍA.

- No asumir automáticamente que la proforma de menor valor debe ser
  seleccionada si no cumple las condiciones establecidas en los
  TDR o especificaciones técnicas.

4. CONTRATACIONES SUPERIORES A USD 10.000
- Identificar la metodología utilizada para determinar el presupuesto.

- Verificar que las fuentes utilizadas sean pertinentes y comparables.

- Verificar que exista información suficiente para comprender cómo
  se obtuvo el presupuesto referencial.

- Revisar los cálculos utilizados para obtener el valor final.

- Identificar el tipo de procedimiento cuando sea necesario para
  determinar las reglas aplicables.

- No asumir requisitos normativos específicos únicamente por superar
  USD 10.000. Cuando una exigencia dependa del procedimiento, primero
  debe identificarse dicho procedimiento.

5. COMPARABILIDAD
- Verificar que las fuentes o proformas utilizadas correspondan a
  condiciones comparables.

- Identificar diferencias materiales en cantidades, características,
  alcance, unidades, condiciones comerciales o impuestos que puedan
  distorsionar la comparación.

- No generar observaciones por diferencias menores que no afecten
  razonablemente la determinación del presupuesto.

6. PRECIOS Y CÁLCULOS
- Comprobar matemáticamente:
  * cantidades por precios unitarios;
  * subtotales;
  * impuestos;
  * descuentos cuando existan;
  * totales;
  * promedios u otras operaciones utilizadas.

- Cuando exista un error, indicar concretamente:
  * valor utilizado;
  * cálculo realizado;
  * valor obtenido;
  * diferencia encontrada.

- No limitarse a recomendar que el analista revise el cálculo cuando
  el propio documento contenga información suficiente para comprobarlo.

7. VIGENCIA Y PERTINENCIA DE LA INFORMACIÓN
- Verificar las fechas de las proformas, cotizaciones, consultas o
  fuentes utilizadas cuando consten.

- Identificar únicamente problemas de vigencia cuando exista una
  razón concreta para considerar que la información utilizada puede
  afectar la razonabilidad del presupuesto.

8. COHERENCIA CON EL OBJETO
- Verificar que los bienes, servicios, cantidades o componentes
  considerados para determinar el presupuesto correspondan al objeto
  de contratación.

- Identificar componentes incluidos en el presupuesto que no consten
  en el objeto, TDR o especificaciones cuando dicha diferencia sea
  comprobable.

9. RESULTADO DE LA REVISIÓN
- No generar observaciones genéricas.
- No inventar requisitos que no estén sustentados.
- Consolidar errores relacionados en un mismo hallazgo.
- Priorizar errores de cálculo, falta de comparabilidad, diferencias
  materiales, información insuficiente y contradicciones que puedan
  afectar el presupuesto referencial.

REGLA ESPECIAL:
La clasificación HASTA USD 10.000 o SUPERIOR A USD 10.000 sirve para
determinar qué análisis corresponde realizar.

No debes concluir automáticamente que un documento incumple únicamente
por su monto.

Cuando una conclusión dependa de una disposición normativa específica
que no esté disponible en el contexto de la revisión, indica que
requiere verificación normativa en lugar de inventar la regla.
""",

    "PROFORMAS": """
Analiza las PROFORMAS utilizadas dentro del procedimiento.

Revisa especialmente:
- comparabilidad;
- descripción de productos o servicios;
- cantidades;
- precios unitarios y totales;
- impuestos;
- fechas;
- condiciones comerciales;
- posibles diferencias entre proformas;
- errores matemáticos;
- señales de falta de comparabilidad.
""",

    "OTROS_DOCUMENTOS": """
Realiza una revisión técnico-administrativa del documento.

Identifica:
- objeto y finalidad;
- inconsistencias;
- contradicciones;
- información incompleta;
- riesgos;
- datos relevantes para el procedimiento;
- aspectos que deberían ser verificados por el analista.
"""
}
# ============================================================
# BUSCAR NORMATIVA PARA LA REVISIÓN IA
# ============================================================

def buscar_normativa_revision(texto_documento, tipo_documento):
    """
    Recupera normativa vigente y activa relacionada con los temas
    detectados en el documento.

    Utiliza artículos dirigidos para criterios conocidos con el fin
    de evitar enviar normativa irrelevante a la IA.
    """

    conn = get_connection()
    cur = conn.cursor()

    try:

        texto_busqueda = (
            f"{tipo_documento} {texto_documento}"
        ).lower()

        # ---------------------------------------------------------
        # MAPA DE TEMAS -> ARTÍCULOS
        # ---------------------------------------------------------
        # La búsqueda se realiza además por tipo de norma para evitar
        # confundir artículos con igual numeración.
        # ---------------------------------------------------------
        # ============================================================
        # NORMATIVA BASE SEGÚN EL TIPO DE DOCUMENTO
        # ============================================================

        normativa_base = {

            "DETERMINACION_NECESIDAD": {
                "tipo_norma": "REGLAMENTO",
                "articulos": ["65", "74"]
            },

            "PRESUPUESTO_REFERENCIAL": {
                "tipo_norma": "REGLAMENTO",
                "articulos": ["73", "75"]
            },

            "ESPECIFICACIONES_TECNICAS": {
                "tipo_norma": "REGLAMENTO",
                "articulos": ["76", "77"]
            },

            "TERMINOS_REFERENCIA": {
                "tipo_norma": "REGLAMENTO",
                "articulos": ["76", "78"]
            }
        }
        reglas = [

            # =========================================================
            # EXPERIENCIA GENERAL Y ESPECÍFICA
            # =========================================================
            {
                "terminos": [
                    "experiencia general",
                    "experiencia específica",
                    "experiencia especifica"
                ],
                "tipo_norma": "REGLAMENTO",
                "articulos": ["105", "106", "107"]
            },

            # =========================================================
            # DETERMINACIÓN DE LA NECESIDAD / MEJOR VALOR POR DINERO
            # =========================================================
            {
                "terminos": [
                    "determinación de la necesidad",
                    "determinacion de la necesidad",
                    "mejor valor por dinero",
                    "beneficio",
                    "eficiencia",
                    "efectividad"
                ],
                "tipo_norma": "REGLAMENTO",
                "articulos": ["65", "74"]
            },

            # =========================================================
            # PRESUPUESTO REFERENCIAL
            # =========================================================
            {
                "terminos": [
                    "presupuesto referencial",
                    "determinación del presupuesto",
                    "determinacion del presupuesto",
                    "estudio de mercado"
                ],
                "tipo_norma": "REGLAMENTO",
                "articulos": ["73", "75"]
            },

            # =========================================================
            # ESPECIFICACIONES TÉCNICAS
            # =========================================================
            {
                "terminos": [
                    "especificaciones técnicas",
                    "especificaciones tecnicas"
                ],
                "tipo_norma": "REGLAMENTO",
                "articulos": ["76", "77"]
            },

            # =========================================================
            # TÉRMINOS DE REFERENCIA
            # =========================================================
            {
                "terminos": [
                    "términos de referencia",
                    "terminos de referencia"
                ],
                "tipo_norma": "REGLAMENTO",
                "articulos": ["76", "78"]
            },

            # =========================================================
            # EVALUACIÓN DE OFERTAS
            # =========================================================
            {
                "terminos": [
                    "evaluación de ofertas",
                    "evaluacion de ofertas",
                    "metodología de evaluación",
                    "metodologia de evaluacion",
                    "evaluación por puntaje",
                    "evaluacion por puntaje",
                    "puntaje",
                    "puntuación",
                    "puntuacion"
                ],
                "tipo_norma": "REGLAMENTO",
                "articulos": ["84", "105", "107"]
            },

            # # =========================================================
            # # SUBASTA INVERSA ELECTRÓNICA
            # # =========================================================
            # {
            #     "terminos": [
            #         "subasta inversa electrónica",
            #         "subasta inversa electronica",
            #         "subasta inversa",
            #         "sie"
            #     ],
            #     "tipo_norma": "LEY",
            #     "articulos": ["47"]
            # },

            # {
            #     "terminos": [
            #         "subasta inversa electrónica",
            #         "subasta inversa electronica",
            #         "subasta inversa",
            #         "sie"
            #     ],
            #     "tipo_norma": "REGLAMENTO",
            #     "articulos": ["257"]
            # },

            # # =========================================================
            # # LICITACIÓN
            # # =========================================================
            # {
            #     "terminos": [
            #         "licitación",
            #         "licitacion"
            #     ],
            #     "tipo_norma": "LEY",
            #     "articulos": ["48"]
            # },

            # {
            #     "terminos": [
            #         "licitación",
            #         "licitacion"
            #     ],
            #     "tipo_norma": "REGLAMENTO",
            #     "articulos": ["265"]
            # },

            # # =========================================================
            # # ÍNFIMA CUANTÍA
            # # =========================================================
            # {
            #     "terminos": [
            #         "ínfima cuantía",
            #         "infima cuantia"
            #     ],
            #     "tipo_norma": "LEY",
            #     "articulos": ["50"]
            # },

            # {
            #     "terminos": [
            #         "ínfima cuantía",
            #         "infima cuantia"
            #     ],
            #     "tipo_norma": "REGLAMENTO",
            #     "articulos": ["269", "270"]
            # },

            # =========================================================
            # GARANTÍA TÉCNICA
            # =========================================================
            {
                "terminos": [
                    "garantía técnica",
                    "garantia tecnica"
                ],
                "tipo_norma": "LEY",
                "articulos": ["84", "87"]
            },

            # =========================================================
            # GARANTÍA DE FIEL CUMPLIMIENTO
            # =========================================================
            {
                "terminos": [
                    "garantía de fiel cumplimiento",
                    "garantia de fiel cumplimiento"
                ],
                "tipo_norma": "LEY",
                "articulos": ["84", "85"]
            },

            # =========================================================
            # GARANTÍA POR ANTICIPO
            # =========================================================
            {
                "terminos": [
                    "garantía por anticipo",
                    "garantia por anticipo",
                    "anticipo"
                ],
                "tipo_norma": "LEY",
                "articulos": ["84", "86"]
            },
        ]

        criterios = []

        # ============================================================
        # 1. AGREGAR NORMATIVA BASE DEL TIPO DE DOCUMENTO
        # ============================================================

        tipo_documento_normalizado = str(
            tipo_documento or ""
        ).strip().upper()

        base = normativa_base.get(
            tipo_documento_normalizado
        )

        if base:
            criterios.append(base)


        # ============================================================
        # 2. AGREGAR NORMATIVA COMPLEMENTARIA SEGÚN EL CONTENIDO
        # ============================================================

        for regla in reglas:

            if any(
                termino in texto_busqueda
                for termino in regla["terminos"]
            ):
                criterios.append(regla)


        # ============================================================
        # 3. SI NO EXISTE NORMATIVA RELACIONADA
        # ============================================================

        if not criterios:
            return ""

        condiciones = []
        parametros = []

        for criterio in criterios:

            articulos = criterio["articulos"]
            tipo_norma = criterio["tipo_norma"]

            placeholders = ", ".join(["%s"] * len(articulos))

            condiciones.append(
                f"""
                (
                    UPPER(n.tipo_norma) LIKE %s
                    AND a.numero_articulo IN ({placeholders})
                )
                """
            )

            parametros.append(f"%{tipo_norma.upper()}%")
            parametros.extend(articulos)

        where_normativa = " OR ".join(condiciones)

        sql = f"""
            SELECT DISTINCT
                n.nombre,
                n.tipo_norma,
                n.numero_norma,
                a.numero_articulo,
                a.titulo,
                a.contenido
            FROM articulos_normativa_control a
            JOIN normativas_control n
                ON n.id = a.normativa_id
            WHERE
                n.vigente = TRUE
                AND a.activo = TRUE
                AND (
                    {where_normativa}
                )
            ORDER BY
                n.nombre,
                a.numero_articulo
        """

        cur.execute(sql, parametros)

        articulos = cur.fetchall()

        bloques = []

        for articulo in articulos:

            nombre = articulo[0]
            tipo_norma = articulo[1]
            numero_norma = articulo[2]
            numero_articulo = articulo[3]
            titulo = articulo[4]
            contenido = articulo[5]

            bloques.append(
                f"""
NORMA: {nombre}
TIPO: {tipo_norma or ''}
NÚMERO: {numero_norma or ''}
ARTÍCULO: {numero_articulo}
TÍTULO: {titulo or ''}

CONTENIDO:
{contenido or ''}
""".strip()
            )

        return "\n\n-------------------------\n\n".join(bloques)

    finally:
        cur.close()
        conn.close()


def construir_prompt(tipo_documento,texto_documento,tipo_procedimiento=None):

    criterio = CRITERIOS_DOCUMENTO.get(
        tipo_documento,
        CRITERIOS_DOCUMENTO["OTROS_DOCUMENTOS"]
    )

    normativa_relevante = buscar_normativa_revision(
        texto_documento,
        tipo_documento
        
    )
    
    return f"""
Eres un asistente especializado en control previo y revisión técnica
de documentación de contratación pública.

Tu función es apoyar a un analista humano de contratación pública.

TIPO DE DOCUMENTO:
{tipo_documento}
TIPO DE PROCEDIMIENTO:
{tipo_procedimiento if tipo_procedimiento else "NO INFORMADO POR SICOP"}

REGLA SOBRE EL PROCEDIMIENTO:

- Si SICOP informa expresamente un TIPO DE PROCEDIMIENTO, este dato
  corresponde al procedimiento real asociado al expediente y tendrá
  prioridad para la revisión.

- Si SICOP NO informa el tipo de procedimiento, revisa si el propio
  documento identifica de forma EXPRESA, DIRECTA E INEQUÍVOCA el
  procedimiento actual de contratación.

- Se considera identificación expresa cuando el documento utiliza
  expresiones que claramente presentan el procedimiento como el
  procedimiento que se está preparando o ejecutando, por ejemplo:
  "Tipo de procedimiento: ...",
  "Procedimiento de contratación: ...",
  "Licitación de Seguros",
  "Subasta Inversa Electrónica",
  u otra declaración equivalente claramente asociada al expediente.

- Cuando el procedimiento esté identificado expresamente en el
  documento, puedes utilizarlo para realizar la revisión documental,
  indicando, cuando sea necesario, que corresponde al
  "procedimiento declarado en el documento".

- NO generes un hallazgo únicamente porque SICOP no tenga registrado
  el tipo de procedimiento cuando este se encuentre identificado
  de forma expresa e inequívoca en el documento revisado.

- NO determines el procedimiento únicamente por menciones incidentales
  a nombres de procedimientos.

- Las referencias a Subasta Inversa Electrónica, Licitación,
  Ínfima Cuantía u otros procedimientos que aparezcan dentro de:
  comparaciones, análisis de mejor valor por dinero, antecedentes,
  citas normativas, explicaciones o alternativas de contratación,
  NO constituyen por sí mismas identificación del procedimiento actual.

- Si SICOP no informa el procedimiento y el documento tampoco lo
  identifica de forma expresa e inequívoca, entonces considera el
  procedimiento como NO DETERMINADO.

- Solo cuando conocer el procedimiento sea indispensable para verificar
  objetivamente un requisito concreto, y este no pueda determinarse
  ni desde SICOP ni desde el documento, podrás generar una observación
  indicando específicamente qué aspecto no puede verificarse.

- NO generes observaciones preventivas o genéricas por la sola ausencia
  del tipo de procedimiento.
CRITERIOS ESPECÍFICOS DE REVISIÓN:
{criterio}
NORMATIVA DISPONIBLE EN SICOP:
--------------------------------------------------
{normativa_relevante if normativa_relevante else "No se recuperó normativa específica para esta revisión."}
--------------------------------------------------

REGLAS PARA UTILIZAR LA NORMATIVA:

- La normativa anterior proviene de la base normativa almacenada
  en SICOP.

- Cuando un hallazgo tenga relación directa con uno de los artículos
  proporcionados, debes citar la norma y el número de artículo.

- NO cites un artículo únicamente porque contenga palabras similares.
  Debes comprobar que su contenido realmente sustente la observación.

- NO inventes números de artículos.

- NO utilices como fundamento un artículo que no haya sido
  proporcionado en la NORMATIVA DISPONIBLE EN SICOP.

- Si ninguno de los artículos proporcionados sustenta directamente
  un hallazgo, escribe:
  "Requiere verificación normativa".

- La normativa proporcionada NO obliga a generar un hallazgo.
  Primero debe existir un problema concreto en el documento.
REGLAS OBLIGATORIAS DE REVISIÓN:

1. Debes revisar OBLIGATORIAMENTE TODOS los aspectos establecidos
   en los CRITERIOS ESPECÍFICOS DE REVISIÓN.

   Ningún criterio específico puede omitirse aunque ya hayas
   identificado varios hallazgos importantes.

   El límite de hallazgos limita únicamente la cantidad de problemas
   que se reportan, NO la cantidad de criterios que debes analizar.

2. Antes de redactar el resultado, realiza internamente una revisión
   completa de cada criterio específico.

   Para cada criterio determina:
   - REVISADO SIN OBSERVACIÓN;
   - REVISADO CON OBSERVACIÓN; o
   - NO VERIFICABLE CON LA INFORMACIÓN DISPONIBLE.

   No es necesario mostrar esta clasificación interna en el informe.
   Utilízala para garantizar que ningún criterio quede sin analizar.

3. NO asumas que falta información cuando esta no sea necesaria para
   la naturaleza concreta de la contratación.

4. NO generes observaciones genéricas, doctrinarias o meramente
   preventivas.

5. Un hallazgo debe existir únicamente cuando haya una inconsistencia,
   contradicción, error de cálculo, requisito restrictivo, falta de
   información necesaria o situación concreta que requiera actuación
   del analista.

6. NO repitas un mismo problema bajo diferentes títulos.

7. Si varios problemas tienen la misma causa, consolídalos en un
   solo hallazgo.

8. Prioriza los hallazgos de mayor importancia para la continuidad,
   legalidad, objetividad, competencia o correcta ejecución del
   procedimiento.

9. NO describas extensamente aquello que se encuentra correcto.

10. Cuando exista información numérica suficiente, realiza la
    comprobación o cálculo correspondiente. No te limites a recomendar
    que el analista lo verifique.

11. Cuando identifiques una contradicción, indica concretamente cuáles
    son los datos o disposiciones que se contradicen.

12. EXPERIENCIA GENERAL Y ESPECÍFICA

- Identificar primero el presupuesto referencial.

- Si el presupuesto referencial es HASTA USD 10.000 y corresponde
  a ÍNFIMA CUANTÍA:

  * No aplicar automáticamente los parámetros de experiencia
    utilizados para procedimientos con evaluación por puntaje.

  * Si los TDR exigen experiencia, verificar que esta sea necesaria,
    razonable y proporcional al objeto de contratación.

  * Verificar que se determine claramente la experiencia requerida
    y sus medios de acreditación.

  * La experiencia requerida deberá poder verificarse objetivamente
    como CUMPLE / NO CUMPLE.

  * NO asignar puntaje por experiencia.

- Si el presupuesto referencial SUPERA USD 10.000:

  * Identificar primero el tipo de procedimiento.

  * Identificar los montos o porcentajes exigidos para experiencia
    general y específica cuando estos correspondan al procedimiento.

  * Cuando resulte aplicable, verificar los valores establecidos
    conforme a la tabla del artículo 106 del Reglamento.

  * Cuando existan datos suficientes y la regla normativa aplicable
    esté disponible, realizar el cálculo y comparar el resultado con
    lo establecido en el documento.

  * Si existe diferencia, mostrar concretamente el valor establecido
    y el valor obtenido en la comprobación.

  * Verificar que existan medios objetivos de acreditación.

- NO observar la ausencia de experiencia general o específica
  únicamente porque no conste en el documento.
  Primero determina si corresponde exigirla según la naturaleza
  y procedimiento de la contratación.

13. METODOLOGÍA DE EVALUACIÓN

PRIMERO debes identificar el presupuesto referencial y determinar
qué regla de revisión corresponde.

A. CONTRATACIONES DE ÍNFIMA CUANTÍA HASTA USD 10.000:

- NO exigir una metodología de evaluación por puntaje propia de
  licitación, concurso público u otros procedimientos que utilicen
  evaluación por puntaje.

- Verificar que los requisitos establecidos en los TDR permitan
  determinar objetivamente si una proforma CUMPLE o NO CUMPLE
  con las condiciones requeridas.

- La revisión de la proforma debe permitir comprobar el cumplimiento
  de las condiciones técnicas, económicas y demás requisitos
  establecidos en los TDR.

- Si los TDR exigen EXPERIENCIA, verificar:
  * que sea pertinente y proporcional al objeto de contratación;
  * que se determine claramente qué experiencia se requiere;
  * que se establezcan medios objetivos para acreditarla;
  * que pueda evaluarse como CUMPLE / NO CUMPLE;
  * NO asignar puntaje por experiencia.

- Si los TDR exigen PERSONAL TÉCNICO, verificar:
  * que sea necesario para la naturaleza del servicio;
  * que se identifiquen claramente los perfiles requeridos;
  * que se establezcan los requisitos que deberán acreditar;
  * que existan medios objetivos de verificación;
  * evaluar como CUMPLE / NO CUMPLE;
  * NO asignar puntaje.

- Si los TDR exigen EQUIPO MÍNIMO, verificar:
  * que sea necesario para ejecutar el objeto;
  * que los equipos estén claramente identificados;
  * que existan medios objetivos para acreditar su disponibilidad;
  * evaluar como CUMPLE / NO CUMPLE;
  * NO asignar puntaje.

- NO exigir experiencia, personal técnico o equipo mínimo únicamente
  por tratarse de una contratación pública.
  Estos requisitos deben guardar relación con la naturaleza,
  complejidad y objeto de la contratación.

- Entre las proformas recibidas deberán considerarse aquellas que
  CUMPLAN con los requisitos establecidos en los TDR.

- NO recomendar la creación de matrices de puntuación para una
  contratación de ínfima cuantía.

B. CONTRATACIONES SUPERIORES A USD 10.000:

- Identificar el tipo de procedimiento de contratación.

- Determinar si el procedimiento aplicable contempla únicamente
  evaluación CUMPLE / NO CUMPLE o también una etapa de evaluación
  POR PUNTAJE.

- Cuando corresponda evaluación por puntaje, verificar que la
  metodología sea coherente con el modelo de pliego aplicable al
  procedimiento correspondiente.

- Verificar que los parámetros puntuables sean objetivos, medibles
  y verificables.

- Verificar que cada parámetro establezca claramente su medio de
  acreditación.

- Verificar que las fórmulas, escalas y reglas de puntuación puedan
  aplicarse objetivamente.

- Identificar contradicciones entre requisitos mínimos evaluados como
  CUMPLE / NO CUMPLE y parámetros posteriormente evaluados por puntaje.

- NO asumir que todo procedimiento superior a USD 10.000 utiliza
  evaluación por puntaje. Primero debe identificarse el procedimiento
  aplicable.

14. Utiliza lenguaje técnico, concreto y breve.

15. Genera un MÁXIMO DE 10 HALLAZGOS.
    Si existen más situaciones, selecciona y consolida las de mayor
    relevancia.
    
    Si existen observaciones materiales en diferentes criterios específicos,
    procura que los hallazgos representen los distintos criterios afectados.

    No concentres todos los hallazgos en un solo componente del documento
    si existen problemas relevantes en otros componentes obligatorios.

    El límite máximo de hallazgos NO autoriza a omitir la revisión de
    metodología, productos o servicios, plazo, forma de pago, obligaciones,
    personal técnico, equipos, experiencia, evaluación u otros criterios
    expresamente establecidos para el tipo de documento.

16. Cada hallazgo debe contener la observación y la acción requerida.
    NO vuelvas a crear posteriormente una lista separada de
    recomendaciones que repita los mismos asuntos.
    
17. La ACCIÓN REQUERIDA debe limitarse a indicar QUÉ aspecto del
    documento debe corregirse, aclararse, completarse, armonizarse
    o verificarse.

    La ACCIÓN REQUERIDA NO debe redactar, diseñar ni imponer la
    solución técnica que deberá adoptar la unidad requirente.

    NO debes crear por cuenta propia:
    - especificaciones técnicas;
    - metodologías de trabajo;
    - entregables o productos;
    - requisitos de experiencia;
    - perfiles de personal;
    - equipos mínimos;
    - coberturas;
    - deducibles;
    - porcentajes;
    - fórmulas;
    - escalas de puntuación;
    - condiciones contractuales; ni
    - cualquier otro requisito cuya definición corresponda
      técnicamente a la unidad requirente.

    Cuando detectes que falta definición o precisión, indica el
    aspecto que debe ser revisado y la razón por la cual afecta
    la claridad, verificabilidad, coherencia o cumplimiento del
    documento.

    Cuando corresponda, puedes señalar los elementos del documento
    que presentan contradicción o insuficiencia, pero SIN establecer
    cuál debe ser el contenido técnico definitivo.

    Los ejemplos solo podrán utilizarse para explicar un hallazgo
    y deberán identificarse expresamente como REFERENCIALES.

    La responsabilidad de definir la solución técnica corresponde
    a la unidad requirente.

DOCUMENTO A REVISAR:
--------------------------------------------------
{texto_documento}
--------------------------------------------------

DEVUELVE EXACTAMENTE ESTA ESTRUCTURA:

## RESULTADO DE LA REVISIÓN

### HALLAZGO 1
NIVEL: ALTO / MEDIO / BAJO
ASPECTO:
OBSERVACIÓN:
ACCIÓN REQUERIDA:
NORMATIVA:
- Si existe sustento directo en la NORMATIVA DISPONIBLE EN SICOP,
  indicar el nombre de la norma, número de artículo y explicar
  brevemente su relación con el hallazgo.
- Si los artículos proporcionados no sustentan directamente el
  hallazgo, escribir "Requiere verificación normativa".
- NO inventar artículos ni utilizar normativa que no haya sido
  proporcionada.

### HALLAZGO 2
Utiliza la misma estructura.

Continúa únicamente con los hallazgos realmente necesarios,
sin superar 10.

Si no existen observaciones materiales, escribe:

SIN OBSERVACIONES RELEVANTES

## CONCLUSIÓN

Indica únicamente una de las siguientes opciones:

- SIN OBSERVACIONES RELEVANTES
- CON OBSERVACIONES
- REQUIERE REVISIÓN ADICIONAL

Agrega después una explicación de máximo 3 líneas.
"""



def analizar_documento_control(
    tipo_documento,
    texto_documento,
    tipo_procedimiento=None
):

    # ============================================================
    # VALIDAR TEXTO DEL DOCUMENTO
    # ============================================================
    if not texto_documento or not texto_documento.strip():
        raise ValueError(
            "No se encontró texto suficiente para realizar el análisis."
        )


    # ============================================================
    # OBTENER API KEY
    # ============================================================
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "No está configurada la variable OPENAI_API_KEY."
        )


    # ============================================================
    # CREAR CLIENTE OPENAI
    # Se crea solamente cuando realmente se utiliza la IA.
    # ============================================================
    client = OpenAI(
        api_key=api_key
    )


    # ============================================================
    # CONSTRUIR PROMPT SEGÚN TIPO DE DOCUMENTO Y PROCEDIMIENTO
    # ============================================================
    prompt = construir_prompt(
        tipo_documento,
        texto_documento,
        tipo_procedimiento
    )


    # ============================================================
    # ANALIZAR DOCUMENTO
    # ============================================================
    response = client.responses.create(
        model="gpt-5.6-terra",
        input=prompt
    )


    # ============================================================
    # DEVOLVER RESULTADO
    # ============================================================
    resultado = response.output_text

    if not resultado or not resultado.strip():
        raise ValueError(
            "La IA no devolvió un resultado de análisis."
        )

    return resultado.strip()