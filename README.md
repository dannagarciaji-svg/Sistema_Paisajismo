# VerdeVivo · Sistema de Gestión de Servicios de Paisajismo

Aplicación web full-stack para administrar clientes, propiedades, contratos de servicios, personal, visitas de mantenimiento e insumos de jardinería. El frontend es una SPA en HTML/CSS/JavaScript y el backend es una API REST en Flask conectada a **MongoDB Atlas** mediante el driver oficial `pymongo`.

> **Proyecto final — Bases de Datos II**
> Sistema de Gestión de Servicios de Paisajismo, Mantenimiento de Jardines y Control Botánico.

---

## 1. Enlaces de entrega

| Elemento | Enlace |
|---|---|
| Aplicación desplegada | `[PENDIENTE: URL pública de Render]` |
| Repositorio público | [https://github.com/dannagarciaji-svg/Sistema_Paisajismo](https://github.com/dannagarciaji-svg/Sistema_Paisajismo) |
| Documentación técnica | [`docs/Documentacion_Tecnica_Sistema_Paisajismo.md`](docs/Documentacion_Tecnica_Sistema_Paisajismo.md) |
| Documento entregable (DOCX) | [`docs/Documentacion_Tecnica_Sistema_Paisajismo.docx`](docs/Documentacion_Tecnica_Sistema_Paisajismo.docx) |
| Evidencias gráficas | [`docs/evidencias/`](docs/evidencias/) |

Los enlaces de Render y GitHub se completan después de publicar el proyecto. Las credenciales de MongoDB Atlas **no** se almacenan en el repositorio: se configuran como variables de entorno.

---

## 2. Funcionalidades principales

- **CRUD completo** de las seis entidades del dominio:
  - `clientes`
  - `propiedades` (con especies botánicas embebidas)
  - `servicios_contratos` (con servicios embebidos y valor total calculado)
  - `personal`
  - `visitas_mantenimiento` (con personal e insumos referenciados)
  - `insumos`
- **Búsqueda y filtros** por texto, estado, ciudad, tipo, cargo, rango de fechas, cliente, contrato, personal y nivel de stock.
- **Relaciones legibles**: las tablas muestran nombres de clientes, propiedades, contratos y trabajadores en lugar de ObjectIds.
- **Panel general** con indicadores: clientes activos, propiedades, área gestionada, contratos activos, cartera, visitas, cumplimiento, personal e insumos críticos.
- **Cinco consultas analíticas** con Aggregation Pipeline:
  1. Clientes y sus propiedades (`$lookup`, `$addFields`, `$project`, `$sort`).
  2. Visitas con detalle de propiedad, cliente y contrato (tres `$lookup` encadenados).
  3. Distribución de visitas por estado (`$facet`, `$group`, `$sort`).
  4. Ranking de insumos más utilizados (`$unwind`, `$group`, `$lookup`, `$sort`, `$limit`).
  5. Servicios más contratados (`$unwind`, `$group`, `$project`, `$sort`).
- **Gráficos** con Chart.js y reportes en tablas.
- **Control automático de inventario**: las visitas en estado `En proceso` o `Finalizada` descuentan existencias de forma atómica; al editar, cancelar o eliminar una visita el stock se ajusta o se repone.
- **Validaciones de negocio** en backend y frontend.
- **Diseño responsive** en español, sin paso de compilación.

---

## 3. Arquitectura

```text
Navegador (SPA HTML/CSS/JS + Chart.js)
        │  fetch / JSON
        ▼
Flask (app.py + blueprints por entidad)
        │  pymongo
        ▼
MongoDB Atlas (jardineria_db)
```

![Arquitectura](docs/diagramas/arquitectura.png)

### Estructura del proyecto

```text
Sistema_Paisajismo/
├── app.py                      # Punto de entrada Flask y manejo de errores
├── backend/
│   ├── config.py               # Conexión única a MongoDB Atlas
│   ├── inventario.py           # Ajuste atómico de existencias
│   ├── utils.py                # Serialización, ObjectId y errores API
│   ├── validators.py           # Reglas y validaciones compartidas
│   └── routes/
│       ├── clientes.py
│       ├── propiedades.py
│       ├── servicios_contratos.py
│       ├── personal.py
│       ├── visitas_mantenimiento.py
│       ├── insumos.py
│       └── analitica.py        # 5 pipelines + KPIs
├── frontend/
│   ├── index.html
│   ├── css/estilos.css
│   └── js/{api,formularios,vistas,app}.js
├── pruebas/smoke_test.py       # 28 pruebas de integración
├── docs/                       # Documentación, diagramas y evidencias
├── seed.py                     # Datos de demostración e índices
├── requirements.txt
├── requirements-dev.txt
├── Procfile
├── render.yaml
└── .env.example
```

---

## 4. Ejecución local

### Requisitos

- Python 3.11 o superior (probado con Python 3.13).
- Una base de datos en MongoDB Atlas y su cadena de conexión.

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/dannagarciaji-svg/Sistema_Paisajismo.git
cd Sistema_Paisajismo

# 2. Crear y activar el entorno virtual
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements-dev.txt

# 4. Configurar credenciales
copy .env.example .env        # Windows
cp .env.example .env          # Linux/macOS
# Edite .env con su MONGO_URI y MONGO_DB

# 5. (Opcional) Cargar datos de demostración
python seed.py

# 6. Ejecutar la aplicación
flask --app app run --port 5000
```

Abrir `http://127.0.0.1:5000`.

### Variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `MONGO_URI` | Cadena de conexión de MongoDB Atlas | `mongodb+srv://usuario:clave@cluster.mongodb.net/?retryWrites=true&w=majority` |
| `MONGO_DB` | Nombre de la base de datos | `jardineria_db` |

---

## 5. Pruebas de integración

Con el servidor en ejecución:

```bash
python pruebas/smoke_test.py http://127.0.0.1:5000
```

El script valida conexión, consultas, filtros, CRUD, reglas de negocio, integridad referencial, inventario y las cinco consultas analíticas. Resultado esperado: **28/28 pruebas aprobadas**.

> Las pruebas crean y eliminan sus propios registros. Si se interrumpen, ejecute `python seed.py` para restaurar los datos de demostración.

---

## 6. API REST

Todas las respuestas de listado usan la forma `{"datos": [...], "total": n}`. Los errores usan `{"error": "...", "detalles": [...]}`.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Estado de la conexión y conteo por colección |
| GET/POST | `/clientes` | Listar/crear clientes |
| GET/PUT/DELETE | `/clientes/<id>` | Consultar/actualizar/eliminar cliente |
| GET/POST | `/propiedades` | Listar/crear propiedades |
| GET/PUT/DELETE | `/propiedades/<id>` | Consultar/actualizar/eliminar propiedad |
| GET | `/propiedades/<id>/historial` | Historial de visitas de la propiedad |
| GET/POST | `/servicios_contratos` | Listar/crear contratos |
| GET/PUT/DELETE | `/servicios_contratos/<id>` | Consultar/actualizar/eliminar contrato |
| GET/POST | `/personal` | Listar/crear trabajadores |
| GET/PUT/DELETE | `/personal/<id>` | Consultar/actualizar/eliminar trabajador |
| GET/POST | `/visitas_mantenimiento` | Listar/crear visitas |
| GET/PUT/DELETE | `/visitas_mantenimiento/<id>` | Consultar/actualizar/eliminar visita |
| GET/POST | `/insumos` | Listar/crear insumos |
| GET/PUT/DELETE | `/insumos/<id>` | Consultar/actualizar/eliminar insumo |
| GET | `/analitica/clientes-propiedades` | Reporte 1 |
| GET | `/analitica/visitas-detalle` | Reporte 2 |
| GET | `/analitica/visitas-estado` | Reporte 3 |
| GET | `/analitica/insumos-mas-utilizados` | Reporte 4 |
| GET | `/analitica/servicios-mas-contratados` | Reporte 5 |
| GET | `/analitica/kpis` | Indicadores del panel |

### Filtros destacados

- `/clientes?q=texto&estado=Activo`
- `/propiedades?q=Rosa&ciudad=Medellín&tipo_propiedad=Casa&cliente_id=<id>`
- `/servicios_contratos?estado=Activo&vigente=true&cliente_id=<id>`
- `/personal?cargo=Jardinero&especialidad=riego`
- `/visitas_mantenimiento?estado=Programada&desde=2026-11-01&hasta=2026-11-30&personal_id=<id>`
- `/insumos?bajo_stock=true`

---

## 7. Reglas de negocio implementadas

1. Documento único por cliente y por trabajador.
2. Correo, teléfono, documento y fechas con formato válido.
3. Enumeraciones cerradas para estados, tipos, cargos y unidades.
4. Una propiedad debe pertenecer a un cliente existente.
5. Un contrato debe pertenecer a un cliente existente y tener al menos un servicio.
6. `valor_total` se calcula como la suma de los precios de los servicios embebidos.
7. `fecha_fin` debe ser posterior a `fecha_inicio`.
8. Una visita solo puede programarse sobre un contrato `Activo`, del mismo cliente de la propiedad y dentro de su vigencia.
9. El personal asignado debe existir, estar activo y no repetirse.
10. Solo visitas `En proceso` o `Finalizada` pueden consumir insumos.
11. El consumo no puede superar las existencias; el descuento es atómico.
12. El estado del insumo (`Disponible`, `Bajo stock`, `Agotado`) se deriva de existencias y stock mínimo.
13. No se elimina un cliente con propiedades o contratos, una propiedad con visitas, un contrato con visitas, un trabajador asignado o un insumo con consumos.
14. Al eliminar una visita se repone el inventario consumido.

---

## 8. Despliegue en Render

1. Suba el proyecto a un repositorio público de GitHub.
2. En [Render](https://render.com), cree un **New Web Service** y conecte el repositorio.
3. Render detecta `render.yaml` o use:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
4. En **Environment Variables** agregue:
   - `MONGO_URI` = cadena de conexión de Atlas.
   - `MONGO_DB` = `jardineria_db`.
5. En MongoDB Atlas, habilite el acceso de red desde `0.0.0.0/0` (o el rango de Render) y verifique el usuario de base de datos.
6. Despliegue y compruebe `https://<servicio>.onrender.com/api/health`.

El archivo `.env` está excluido por `.gitignore`; nunca se publica.

---

## 9. Documentación y evidencias

- [Documentación técnica completa (Markdown)](docs/Documentacion_Tecnica_Sistema_Paisajismo.md)
- [Documento entregable (DOCX)](docs/Documentacion_Tecnica_Sistema_Paisajismo.docx)
- [Diagrama del modelo de datos](docs/diagramas/modelo_datos.png)
- [Diagrama de arquitectura](docs/diagramas/arquitectura.png)
- [Capturas de pantalla](docs/evidencias/)

Para regenerar los recursos de documentación:

```bash
# Diagramas de arquitectura y modelo de datos
python docs/generar_diagramas.py

# Documento DOCX a partir del Markdown
python docs/generar_docx.py
```

---

## 10. Créditos

Proyecto académico de **Bases de Datos II**.
Autor: **Danna Paulina García Jiménez**.
Tecnologías: Flask · MongoDB Atlas · PyMongo · Chart.js · HTML/CSS/JavaScript · Render.
