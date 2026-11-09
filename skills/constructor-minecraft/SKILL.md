---
name: "constructor-minecraft"
description: "Úsala siempre que haya que diseñar o generar cualquier construcción, schematic (.schem) o pixel art de Minecraft: principios de simetría, proporción y decoración, y verificación antes de entregar."
---

# Constructor de Minecraft

Vale para cualquier encargo: un edificio, una casa, una arena, una plaza, un spawn, una ciudad, una mina, un pixel art o una decoración suelta. Los principios de la sección 1 son obligatorios en todas.

## 1. Principios de diseño

### Simetría y armonía
- Antes de colocar un solo bloque, define los ejes: el eje global de la construcción y el eje local de cada parte (fachada, sala, plaza, torre, ventana, puerta).
- Todo lo que se centra sobre un eje queda exactamente centrado. Si un centro sale con decimales, el tamaño está mal elegido: corrige las medidas en vez de redondear.
- Paridad coherente. Todos los elementos que comparten un eje tienen la misma paridad. Un camino impar (con bloque central) obliga a que puertas, fuentes, arcos, ventanas, pilares centrales, escaleras y zonas alineadas también sean impares. Por defecto, elige impar, porque tiene bloque central. Nunca mezcles par e impar en el mismo eje.
- Las puertas, entradas y aperturas van centradas en su fachada.
- Las repeticiones (ventanas, columnas, farolas, almenas, puestos) se reparten con la misma separación y de forma simétrica respecto al eje. Calcula el número y el paso para que cuadren con la longitud; que no sobre un hueco en un extremo.
- Si una cantidad no reparte igual (por ejemplo, 14 entre 4), dilo y reparte en espejo (las partes opuestas, iguales).
- Las asimetrías solo se permiten cuando son intencionadas y se explican: un elemento orgánico, una ruina, un árbol.
- Al encajar piezas que ya existen (otro schematic, una estructura del mundo), alinea por el centro real de lo construido y no por el rectángulo del fichero. Mide el contorno de la estructura, sin contar su suelo ni su relleno, antes de reservarle el hueco.

### Proporción y volumen
- Evita lo plano. Varía las alturas: zócalos, escalones, plataformas elevadas o hundidas, cornisas y voladizos, tejados con pendiente y remates.
- En las fachadas, da profundidad: pilares que sobresalgan, ventanas retranqueadas, marcos y alféizares, contraventanas, balcones.
- Jerarquía: un elemento principal por zona (el foco) y elementos secundarios que lo acompañen.

### Detalle y variedad
- Ninguna superficie grande de un solo bloque. Trabaja con 3 o 4 materiales por superficie (base, acento, borde, detalle): patrones de suelo, cenefas, degradados, bloques desgastados o mezclados.
- Combina tipos de decoración y no repitas siempre la misma pieza. Usa iluminación de varios diseños, mobiliario (bancos, mesas, mostradores), vegetación de varias especies y alturas, agua (fuentes de varios niveles, estanques, canales), elementos verticales (columnas, antenas, estandartes, monolitos) y señalética.
- Usa bloques de detalle: losas, escaleras, muros, vallas, trampillas, botones, cadenas, faroles, macetas, cabezas, alfombras.
- Cada zona tiene su identidad (una entrada marcada, una pieza central, un borde definido) dentro de la armonía del conjunto.
- La iluminación forma parte del diseño: integrada (en suelos, techos y pilares) y suficiente para que no aparezcan mobs donde no debe.

### Estética
- Por defecto, la que defina el `CLAUDE.md` del proyecto (paleta, tema del servidor). Si no hay ninguna, pregunta o elige una coherente y dilo.
- Si el encargo pide otro estilo, manda el encargo.

## 2. Procedimiento
1. **Aclara el encargo:** tamaño, uso, estilo, orientación (Z+ = sur), qué debe quedar vacío y dónde se pegará. Pregunta solo lo que cambie el diseño.
2. **Planifica en números:** escribe las medidas y posiciones como constantes y declara los ejes y la paridad de cada uno. Pasa las comprobaciones de la sección 3 al plano antes de construir.
3. **Construye por partes**, con piezas reutilizables y parametrizadas (muros, tejados, puertas, ventanas, farolas, árboles...). Los muros se construyen como anillo: nunca una caja hueca de 1 de alto, porque rellena suelo y techo.
4. **Verifica** con las comprobaciones automáticas y revisa las vistas con texturas de cada parte con detalle. Corrige antes de entregar.
5. **Entrega:** el .schem en la carpeta de FAWE del servidor que toque, la vista previa, las instrucciones exactas de pegado (dónde ponerse, hacia dónde mirar, con `-a` o sin él) y los datos útiles (lista de materiales, coordenadas de parcelas o regiones). Añade la entrada en `docs/CHANGELOG.md`.

## 3. Comprobaciones automáticas (siempre; nunca a ojo)
- **Paridad y centrado:** el centro de cada elemento declarado como centrado es entero y coincide con el de su eje.
- **Simetría espejo:** cada parte declarada simétrica se compara con su reflejo, normalizando las orientaciones (facing este/oeste, hinge, shape izquierda/derecha). El objetivo es 0 diferencias, salvo las que estén justificadas.
- **Piezas externas:** el centro real coincide con el centro de su hueco.
- **Recuentos y solapes:** de todo lo que el encargo cuantifica.
- **Ida y vuelta del fichero:** releer el .schem y compararlo bloque a bloque.

## 4. Reglas técnicas
- **Formato:** Sponge v3 con la `DataVersion` del servidor de destino (compruébala para tu versión de Minecraft). `Offset` es la esquina mínima relativa a los pies del jugador. En los schematics v2, el pegado usa `Metadata.WEOffsetX/Y/Z`.
- **Física:** FAWE pega sin físicas, así que hay que calcular antes las conexiones de paneles, vallas, muros y barrotes y la forma de las escaleras en esquina.
- **Estados:** hojas siempre con `persistent=true`. Los estados van normalizados a 'true'/'false' en minúsculas. Valida todos los bloques contra el catálogo de bloques de la versión antes de escribir.
- **Block entities** (spawners, cofres, carteles): con sus datos completos. Los spawners de animales necesitan hierba y luz ≥ 9.
- **Copyright:** no reproducir personajes, mobs ni logos de terceros.
- **Herramientas:** necesitas un generador/lector de schematics (Python u otro). Esta skill no incluye el motor; usa el que tengas en tu proyecto o créalo antes de empezar.
