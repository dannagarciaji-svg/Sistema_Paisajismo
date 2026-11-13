# ============================================================
#  Semilla de datos de demostración - jardineria_db
#  Ejecutar:  python seed.py
#  ADVERTENCIA: elimina y vuelve a crear los documentos de las
#  seis colecciones del proyecto.
# ============================================================
from datetime import datetime

from backend.config import (
    clientes,
    db,
    insumos,
    personal,
    propiedades,
    servicios_contratos,
    visitas_mantenimiento,
)
from backend.validators import calcular_estado_insumo


def fecha(anio, mes, dia, hora=8, minuto=0):
    return datetime(anio, mes, dia, hora, minuto)


def limpiar():
    for coleccion in (
        visitas_mantenimiento,
        servicios_contratos,
        propiedades,
        clientes,
        personal,
        insumos,
    ):
        coleccion.delete_many({})
    print("Colecciones limpiadas.")


def crear_indices():
    clientes.create_index("documento", unique=True, name="uq_clientes_documento")
    clientes.create_index("nombre")
    clientes.create_index("estado")

    propiedades.create_index("cliente_id")
    propiedades.create_index("ciudad")
    propiedades.create_index("nombre")

    servicios_contratos.create_index("cliente_id")
    servicios_contratos.create_index("estado")
    servicios_contratos.create_index("fecha_inicio")

    personal.create_index("documento", unique=True, name="uq_personal_documento")
    personal.create_index("cargo")

    visitas_mantenimiento.create_index("propiedad_id")
    visitas_mantenimiento.create_index("contrato_id")
    visitas_mantenimiento.create_index("estado")
    visitas_mantenimiento.create_index("fecha_programada")
    visitas_mantenimiento.create_index("personal_asignado.personal_id")
    visitas_mantenimiento.create_index("insumos_utilizados.insumo_id")

    insumos.create_index("nombre")
    insumos.create_index("estado")
    print("Índices creados.")


def sembrar():
    limpiar()

    # ------------------------- CLIENTES -------------------------
    datos_clientes = [
        ("Laura Martínez", "1020304050", "3001234567", "laura.martinez@gmail.com", "Calle 20 #15-30", "Activo"),
        ("Carlos Gómez", "1030405060", "3009876543", "carlos.gomez@gmail.com", "Transversal Inferior #10-20", "Activo"),
        ("Constructora Verde S.A.S.", "900456789", "6044567890", "contacto@constructorverde.com", "Carrera 43A #1-50", "Activo"),
        ("Ana María Restrepo", "1010101010", "3112223344", "ana.restrepo@hotmail.com", "Carrera 70 #44-12", "Activo"),
        ("Hotel Jardines del Norte", "900789123", "6043219876", "reservas@jardinesnorte.com", "Calle 10 #40-20", "Activo"),
        ("Jorge Iván Ospina", "1040506070", "3156667788", "jorge.ospina@gmail.com", "Calle 50 #80-15", "Inactivo"),
        ("María Camila Torres", "1050607080", "3129998877", "camila.torres@gmail.com", "Carrera 25 #10-05", "Activo"),
        ("Urbanización Los Cedros", "900321654", "6045551234", "admin@loscedros.com", "Vía a Rionegro Km 5", "Activo"),
    ]
    ids_clientes = []
    for nombre, documento, telefono, correo, direccion, estado in datos_clientes:
        resultado = clientes.insert_one(
            {
                "nombre": nombre,
                "documento": documento,
                "telefono": telefono,
                "correo": correo,
                "direccion": direccion,
                "estado": estado,
            }
        )
        ids_clientes.append(resultado.inserted_id)

    laura, carlos, constructora, ana, hotel, jorge, camila, urbanizacion = ids_clientes

    # ------------------------ PROPIEDADES -----------------------
    datos_propiedades = [
        {
            "cliente_id": laura,
            "nombre": "Jardín Los Pinos",
            "direccion": "Carrera 45 #20-10",
            "ciudad": "Medellín",
            "tipo_propiedad": "Casa",
            "area_m2": 150,
            "especies": [
                {"nombre_comun": "Rosa", "nombre_cientifico": "Rosa spp.", "cantidad": 12, "ubicacion": "Jardín delantero", "necesidades_cuidado": "Riego frecuente, poda y abono cada 30 días"},
                {"nombre_comun": "Hortensia", "nombre_cientifico": "Hydrangea macrophylla", "cantidad": 6, "ubicacion": "Zona de sombra", "necesidades_cuidado": "Suelo húmedo y sombra parcial"},
                {"nombre_comun": "Césped San Agustín", "nombre_cientifico": "Stenotaphrum secundatum", "cantidad": 90, "ubicacion": "Jardín principal", "necesidades_cuidado": "Corte quincenal y riego moderado"},
            ],
        },
        {
            "cliente_id": carlos,
            "nombre": "Finca El Paraíso",
            "direccion": "Vía Las Palmas Km 12",
            "ciudad": "Envigado",
            "tipo_propiedad": "Finca",
            "area_m2": 500,
            "especies": [
                {"nombre_comun": "Palma Areca", "nombre_cientifico": "Dypsis lutescens", "cantidad": 18, "ubicacion": "Entrada principal", "necesidades_cuidado": "Riego moderado y fertilización semestral"},
                {"nombre_comun": "Limón Tahití", "nombre_cientifico": "Citrus latifolia", "cantidad": 8, "ubicacion": "Huerto", "necesidades_cuidado": "Poda de formación y control de plagas"},
                {"nombre_comun": "Bambú", "nombre_cientifico": "Bambusa vulgaris", "cantidad": 30, "ubicacion": "Cerca perimetral", "necesidades_cuidado": "Control de crecimiento y riego regular"},
            ],
        },
        {
            "cliente_id": constructora,
            "nombre": "Zonas verdes Torre Aurora",
            "direccion": "Carrera 43A #1-50",
            "ciudad": "Medellín",
            "tipo_propiedad": "Conjunto residencial",
            "area_m2": 800,
            "especies": [
                {"nombre_comun": "Ficus", "nombre_cientifico": "Ficus benjamina", "cantidad": 22, "ubicacion": "Zona común", "necesidades_cuidado": "Poda ornamental y riego quincenal"},
                {"nombre_comun": "Lantana", "nombre_cientifico": "Lantana camara", "cantidad": 40, "ubicacion": "Jardines laterales", "necesidades_cuidado": "Poda ligera y exposición al sol"},
                {"nombre_comun": "Césped San Agustín", "nombre_cientifico": "Stenotaphrum secundatum", "cantidad": 600, "ubicacion": "Zonas verdes", "necesidades_cuidado": "Corte quincenal y fertilización"},
            ],
        },
        {
            "cliente_id": ana,
            "nombre": "Jardín Casa de Ana",
            "direccion": "Carrera 70 #44-12",
            "ciudad": "Medellín",
            "tipo_propiedad": "Casa",
            "area_m2": 95,
            "especies": [
                {"nombre_comun": "Orquídea", "nombre_cientifico": "Phalaenopsis spp.", "cantidad": 14, "ubicacion": "Invernadero", "necesidades_cuidado": "Humedad controlada y sustrato especial"},
                {"nombre_comun": "Helecho de Boston", "nombre_cientifico": "Nephrolepis exaltata", "cantidad": 10, "ubicacion": "Terraza", "necesidades_cuidado": "Sombra y riego frecuente"},
            ],
        },
        {
            "cliente_id": hotel,
            "nombre": "Jardines Hotel del Norte",
            "direccion": "Calle 10 #40-20",
            "ciudad": "Bello",
            "tipo_propiedad": "Oficina",
            "area_m2": 1200,
            "especies": [
                {"nombre_comun": "Palma Real", "nombre_cientifico": "Roystonea regia", "cantidad": 16, "ubicacion": "Acceso vehicular", "necesidades_cuidado": "Poda de hojas secas y riego profundo"},
                {"nombre_comun": "Ave del Paraíso", "nombre_cientifico": "Strelitzia reginae", "cantidad": 25, "ubicacion": "Jardín interior", "necesidades_cuidado": "Sol directo y abono orgánico"},
                {"nombre_comun": "Bambú", "nombre_cientifico": "Bambusa vulgaris", "cantidad": 45, "ubicacion": "Zona de piscina", "necesidades_cuidado": "Control de crecimiento"},
            ],
        },
        {
            "cliente_id": jorge,
            "nombre": "Apartamento El Poblado",
            "direccion": "Calle 10 #30-20",
            "ciudad": "Medellín",
            "tipo_propiedad": "Apartamento",
            "area_m2": 60,
            "especies": [
                {"nombre_comun": "Suculentas", "nombre_cientifico": "Echeveria elegans", "cantidad": 18, "ubicacion": "Balcón", "necesidades_cuidado": "Riego escaso y luz indirecta"},
                {"nombre_comun": "Helecho", "nombre_cientifico": "Nephrolepis exaltata", "cantidad": 6, "ubicacion": "Sala", "necesidades_cuidado": "Riego frecuente sin encharcar"},
            ],
        },
        {
            "cliente_id": camila,
            "nombre": "Casa Campestre La Esperanza",
            "direccion": "Vía Sabaneta Km 2",
            "ciudad": "Sabaneta",
            "tipo_propiedad": "Finca",
            "area_m2": 320,
            "especies": [
                {"nombre_comun": "Limonero", "nombre_cientifico": "Citrus limon", "cantidad": 10, "ubicacion": "Huerto", "necesidades_cuidado": "Poda y fertilización orgánica"},
                {"nombre_comun": "Hortensia", "nombre_cientifico": "Hydrangea macrophylla", "cantidad": 20, "ubicacion": "Camino de entrada", "necesidades_cuidado": "Sombra parcial y suelo ácido"},
                {"nombre_comun": "Rosa", "nombre_cientifico": "Rosa spp.", "cantidad": 15, "ubicacion": "Jardín trasero", "necesidades_cuidado": "Poda y control fitosanitario"},
            ],
        },
        {
            "cliente_id": urbanizacion,
            "nombre": "Parque Central Los Cedros",
            "direccion": "Vía Rionegro Km 5",
            "ciudad": "Rionegro",
            "tipo_propiedad": "Parque",
            "area_m2": 2500,
            "especies": [
                {"nombre_comun": "Roble", "nombre_cientifico": "Quercus humboldtii", "cantidad": 35, "ubicacion": "Zona boscosa", "necesidades_cuidado": "Monitoreo fitosanitario y riego de establecimiento"},
                {"nombre_comun": "Césped San Agustín", "nombre_cientifico": "Stenotaphrum secundatum", "cantidad": 1800, "ubicacion": "Zona abierta", "necesidades_cuidado": "Corte y fertilización programada"},
                {"nombre_comun": "Lantana", "nombre_cientifico": "Lantana camara", "cantidad": 70, "ubicacion": "Senderos", "necesidades_cuidado": "Poda y control de crecimiento"},
            ],
        },
        {
            "cliente_id": laura,
            "nombre": "Oficina Administrativa 301",
            "direccion": "Calle 20 #15-30",
            "ciudad": "Medellín",
            "tipo_propiedad": "Oficina",
            "area_m2": 40,
            "especies": [
                {"nombre_comun": "Ficus", "nombre_cientifico": "Ficus benjamina", "cantidad": 4, "ubicacion": "Recepción", "necesidades_cuidado": "Luz indirecta y riego semanal"},
                {"nombre_comun": "Suculentas", "nombre_cientifico": "Echeveria elegans", "cantidad": 8, "ubicacion": "Escritorios", "necesidades_cuidado": "Riego escaso"},
            ],
        },
        {
            "cliente_id": constructora,
            "nombre": "Parque Empresarial Itagüí",
            "direccion": "Carrera 48 #20-114",
            "ciudad": "Itagüí",
            "tipo_propiedad": "Oficina",
            "area_m2": 450,
            "especies": [
                {"nombre_comun": "Bambú", "nombre_cientifico": "Bambusa vulgaris", "cantidad": 60, "ubicacion": "Fachada", "necesidades_cuidado": "Control de crecimiento y riego"},
                {"nombre_comun": "Ficus", "nombre_cientifico": "Ficus benjamina", "cantidad": 12, "ubicacion": "Lobby", "necesidades_cuidado": "Poda ornamental"},
            ],
        },
    ]
    ids_propiedades = []
    for propiedad in datos_propiedades:
        resultado = propiedades.insert_one(propiedad)
        ids_propiedades.append(resultado.inserted_id)

    (
        jardin_los_pinos,
        finca_paraiso,
        torre_aurora,
        casa_ana,
        hotel_norte,
        apartamento_poblado,
        casa_esperanza,
        parque_cedros,
        oficina_301,
        parque_empresarial,
    ) = ids_propiedades

    # ---------------------- SERVICIOS / CONTRATOS ----------------
    datos_contratos = [
        {
            "cliente_id": laura,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Poda, riego y limpieza mensual", "precio_acordado": 650000},
                {"nombre": "Fertilización", "descripcion": "Aplicación de fertilizante NPK trimestral", "precio_acordado": 500000},
            ],
            "fecha_inicio": fecha(2026, 10, 1),
            "fecha_fin": fecha(2027, 9, 30),
            "valor_total": 1150000,
            "estado": "Activo",
        },
        {
            "cliente_id": carlos,
            "servicios": [
                {"nombre": "Diseño paisajístico", "descripcion": "Rediseño integral del jardín principal", "precio_acordado": 1800000},
                {"nombre": "Poda de altura", "descripcion": "Poda técnica de árboles y palmas", "precio_acordado": 700000},
            ],
            "fecha_inicio": fecha(2026, 9, 15),
            "fecha_fin": fecha(2027, 3, 15),
            "valor_total": 2500000,
            "estado": "Activo",
        },
        {
            "cliente_id": constructora,
            "servicios": [
                {"nombre": "Mantenimiento de zonas verdes", "descripcion": "Corte, riego y limpieza de zonas comunes", "precio_acordado": 4200000},
                {"nombre": "Control de plagas", "descripcion": "Monitoreo y aplicación de control fitosanitario", "precio_acordado": 1800000},
            ],
            "fecha_inicio": fecha(2026, 1, 1),
            "fecha_fin": fecha(2026, 12, 31),
            "valor_total": 6000000,
            "estado": "Activo",
        },
        {
            "cliente_id": ana,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Riego, poda y cuidado de orquídeas", "precio_acordado": 600000},
            ],
            "fecha_inicio": fecha(2026, 11, 1),
            "fecha_fin": fecha(2027, 11, 1),
            "valor_total": 600000,
            "estado": "Activo",
        },
        {
            "cliente_id": hotel,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Mantenimiento integral de jardines y zonas comunes", "precio_acordado": 6500000},
                {"nombre": "Riego automatizado", "descripcion": "Instalación y mantenimiento de sistema de riego", "precio_acordado": 1500000},
            ],
            "fecha_inicio": fecha(2026, 10, 1),
            "fecha_fin": fecha(2027, 10, 1),
            "valor_total": 8000000,
            "estado": "Activo",
        },
        {
            "cliente_id": jorge,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Mantenimiento básico de balcón y materas", "precio_acordado": 400000},
            ],
            "fecha_inicio": fecha(2026, 1, 1),
            "fecha_fin": fecha(2026, 12, 31),
            "valor_total": 400000,
            "estado": "Finalizado",
        },
        {
            "cliente_id": camila,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Mantenimiento general de la casa campestre", "precio_acordado": 900000},
                {"nombre": "Poda de altura", "descripcion": "Poda de árboles frutales", "precio_acordado": 450000},
                {"nombre": "Siembra de especies", "descripcion": "Siembra y adecuación de nuevas zonas", "precio_acordado": 500000},
            ],
            "fecha_inicio": fecha(2026, 11, 1),
            "fecha_fin": fecha(2027, 11, 1),
            "valor_total": 1850000,
            "estado": "Activo",
        },
        {
            "cliente_id": urbanizacion,
            "servicios": [
                {"nombre": "Mantenimiento de zonas verdes", "descripcion": "Mantenimiento de 2.500 m² de zonas verdes", "precio_acordado": 9000000},
                {"nombre": "Fertilización", "descripcion": "Plan de fertilización semestral", "precio_acordado": 1500000},
                {"nombre": "Control de plagas", "descripcion": "Monitoreo fitosanitario permanente", "precio_acordado": 1500000},
            ],
            "fecha_inicio": fecha(2026, 7, 1),
            "fecha_fin": fecha(2027, 6, 30),
            "valor_total": 12000000,
            "estado": "Activo",
        },
        {
            "cliente_id": constructora,
            "servicios": [
                {"nombre": "Diseño paisajístico", "descripcion": "Diseño de zonas verdes del parque empresarial", "precio_acordado": 3200000},
            ],
            "fecha_inicio": fecha(2026, 10, 20),
            "fecha_fin": fecha(2027, 4, 20),
            "valor_total": 3200000,
            "estado": "Activo",
        },
        {
            "cliente_id": laura,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Mantenimiento de materas de oficina", "precio_acordado": 480000},
            ],
            "fecha_inicio": fecha(2026, 8, 1),
            "fecha_fin": fecha(2027, 8, 1),
            "valor_total": 480000,
            "estado": "Activo",
        },
    ]
    ids_contratos = []
    for contrato in datos_contratos:
        resultado = servicios_contratos.insert_one(contrato)
        ids_contratos.append(resultado.inserted_id)

    (
        contrato_laura,
        contrato_carlos,
        contrato_constructora,
        contrato_ana,
        contrato_hotel,
        contrato_jorge,
        contrato_camila,
        contrato_urbanizacion,
        contrato_parque_empresarial,
        contrato_oficina,
    ) = ids_contratos

    # --------------------------- PERSONAL ------------------------
    datos_personal = [
        ("Carlos Ramírez", "1098765432", "3104567890", "carlos.ramirez@paisajismo.com", "Jardinero", 1800000, ["Poda de plantas", "Mantenimiento de jardines", "Control de plagas"], "Activo"),
        ("Lucía Pérez", "1012345678", "3209876543", "lucia.perez@paisajismo.com", "Paisajista", 2600000, ["Diseño paisajístico", "Selección de especies", "Siembra"], "Activo"),
        ("Andrés Mejía", "1087654321", "3012223344", "andres.mejia@paisajismo.com", "Especialista botánico", 2900000, ["Control botánico", "Fertilización", "Diagnóstico de plagas"], "Activo"),
        ("Diana Torres", "1023456789", "3145556677", "diana.torres@paisajismo.com", "Jardinera", 1750000, ["Riego", "Siembra", "Mantenimiento de jardines"], "Activo"),
        ("Felipe Cárdenas", "1034567890", "3167778899", "felipe.cardenas@paisajismo.com", "Supervisor", 3200000, ["Supervisión de obras", "Poda de altura", "Seguridad en alturas"], "Activo"),
        ("Sofía Herrera", "1045678901", "3188889900", "sofia.herrera@paisajismo.com", "Auxiliar de jardinería", 1500000, ["Limpieza", "Siembra", "Riego"], "Activo"),
        ("Mauricio López", "1056789012", "3199990011", "mauricio.lopez@paisajismo.com", "Jardinero", 1800000, ["Poda de plantas", "Mantenimiento de jardines"], "Inactivo"),
        ("Valentina Ríos", "1067890123", "3211112233", "valentina.rios@paisajismo.com", "Paisajista", 2550000, ["Diseño de jardines", "Riego automatizado"], "Activo"),
        ("Julián Zapata", "1078901234", "3223334455", "julian.zapata@paisajismo.com", "Especialista botánico", 2850000, ["Control fitosanitario", "Fertilización"], "Activo"),
    ]
    ids_personal = []
    for nombre, documento, telefono, correo, cargo, salario, especialidades, estado in datos_personal:
        resultado = personal.insert_one(
            {
                "nombre": nombre,
                "documento": documento,
                "telefono": telefono,
                "correo": correo,
                "cargo": cargo,
                "salario": salario,
                "especialidades": especialidades,
                "estado": estado,
            }
        )
        ids_personal.append(resultado.inserted_id)

    carlos_r, lucia, andres, diana, felipe, sofia, mauricio, valentina, julian = ids_personal
    nombres_personal = {
        str(carlos_r): "Carlos Ramírez",
        str(lucia): "Lucía Pérez",
        str(andres): "Andrés Mejía",
        str(diana): "Diana Torres",
        str(felipe): "Felipe Cárdenas",
        str(sofia): "Sofía Herrera",
        str(mauricio): "Mauricio López",
        str(valentina): "Valentina Ríos",
        str(julian): "Julián Zapata",
    }

    # --------------------------- INSUMOS -------------------------
    # Las existencias ya reflejan el consumo registrado en las visitas.
    datos_insumos = [
        ("Fertilizante NPK 10-30-10", "Fertilizante granular completo para nutrición de plantas y césped", "Kilogramos", 59, 15),
        ("Abono orgánico", "Compost natural para enriquecer la tierra y mejorar su estructura", "Bultos", 19, 8),
        ("Tierra abonada", "Mezcla de tierra negra y materia orgánica para siembra", "Bultos", 9, 10),
        ("Insecticida foliar", "Producto para el control de insectos en hojas y tallos", "Litros", 15, 5),
        ("Fungicida a base de cobre", "Protector fitosanitario contra hongos en jardines", "Kilogramos", 8, 4),
        ("Semilla de césped San Agustín", "Semilla certificada para resiembra de césped", "Kilogramos", 22, 10),
        ("Sustrato premium", "Sustrato especial para orquídeas y plantas de interior", "Bultos", 20, 6),
        ("Acondicionador de suelo", "Producto para regular el pH y mejorar la absorción de nutrientes", "Litros", 25, 25),
        ("Humus de lombriz", "Abono orgánico de alta concentración nutricional", "Bultos", 0, 5),
    ]
    ids_insumos = {}
    for nombre, descripcion, unidad, existencias, stock_minimo in datos_insumos:
        resultado = insumos.insert_one(
            {
                "nombre": nombre,
                "descripcion": descripcion,
                "unidad_medida": unidad,
                "existencias": existencias,
                "stock_minimo": stock_minimo,
                "estado": calcular_estado_insumo(existencias, stock_minimo),
            }
        )
        ids_insumos[nombre] = resultado.inserted_id

    def insumo(nombre, cantidad):
        return {
            "insumo_id": ids_insumos[nombre],
            "nombre": nombre,
            "cantidad": cantidad,
            "unidad_medida": next(item[2] for item in datos_insumos if item[0] == nombre),
        }

    def asignado(*ids):
        return [{"personal_id": id_personal, "nombre": nombres_personal[str(id_personal)]} for id_personal in ids]

    # --------------------------- VISITAS -------------------------
    datos_visitas = [
        {
            "propiedad_id": jardin_los_pinos,
            "contrato_id": contrato_laura,
            "fecha_programada": fecha(2026, 11, 5, 8, 0),
            "personal_asignado": asignado(carlos_r, diana),
            "actividades_realizadas": ["Poda de rosales", "Corte de césped", "Riego general"],
            "observaciones": ["El jardín se encuentra en buen estado general.", "Se recomienda reforzar el abono en la zona de hortensias."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Fertilizante NPK 10-30-10", 3), insumo("Abono orgánico", 2)],
        },
        {
            "propiedad_id": jardin_los_pinos,
            "contrato_id": contrato_laura,
            "fecha_programada": fecha(2026, 11, 12, 8, 0),
            "personal_asignado": asignado(carlos_r),
            "actividades_realizadas": ["Resiembra de césped en zona delantera"],
            "observaciones": ["Se detectó compactación del suelo en el acceso peatonal."],
            "estado": "En proceso",
            "insumos_utilizados": [insumo("Fertilizante NPK 10-30-10", 2), insumo("Semilla de césped San Agustín", 3)],
        },
        {
            "propiedad_id": jardin_los_pinos,
            "contrato_id": contrato_laura,
            "fecha_programada": fecha(2026, 11, 19, 9, 0),
            "personal_asignado": asignado(diana),
            "actividades_realizadas": ["Riego y revisión de sistema de aspersión"],
            "observaciones": ["Visita de seguimiento programada."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": finca_paraiso,
            "contrato_id": contrato_carlos,
            "fecha_programada": fecha(2026, 10, 28, 7, 30),
            "personal_asignado": asignado(lucia, felipe),
            "actividades_realizadas": ["Poda de palmas", "Adecuación de huerto de limones", "Siembra de cobertura vegetal"],
            "observaciones": ["Se identificaron ramas secas en la palma de la entrada.", "Aplicar abono orgánico en el huerto."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Tierra abonada", 5), insumo("Abono orgánico", 4), insumo("Fertilizante NPK 10-30-10", 4)],
        },
        {
            "propiedad_id": finca_paraiso,
            "contrato_id": contrato_carlos,
            "fecha_programada": fecha(2026, 11, 14, 8, 30),
            "personal_asignado": asignado(lucia),
            "actividades_realizadas": ["Continuidad del diseño del jardín principal"],
            "observaciones": ["Confirmar disponibilidad de especies ornamentales."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": torre_aurora,
            "contrato_id": contrato_constructora,
            "fecha_programada": fecha(2026, 11, 3, 7, 0),
            "personal_asignado": asignado(carlos_r, sofia),
            "actividades_realizadas": ["Corte de césped", "Limpieza de zonas comunes", "Aplicación de insecticida"],
            "observaciones": ["Presencia de hormigas en el jardín lateral."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Fertilizante NPK 10-30-10", 8), insumo("Semilla de césped San Agustín", 15), insumo("Insecticida foliar", 3)],
        },
        {
            "propiedad_id": torre_aurora,
            "contrato_id": contrato_constructora,
            "fecha_programada": fecha(2026, 11, 10, 7, 30),
            "personal_asignado": asignado(andres, sofia),
            "actividades_realizadas": ["Control fitosanitario de ficus", "Aplicación de fungicida"],
            "observaciones": ["Se detectaron hongos foliares leves en dos ficus."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Fungicida a base de cobre", 2), insumo("Insecticida foliar", 2)],
        },
        {
            "propiedad_id": torre_aurora,
            "contrato_id": contrato_constructora,
            "fecha_programada": fecha(2026, 11, 18, 7, 0),
            "personal_asignado": asignado(andres, carlos_r),
            "actividades_realizadas": ["Monitoreo de lantana y ficus"],
            "observaciones": ["Verificar evolución del tratamiento antifúngico."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": casa_ana,
            "contrato_id": contrato_ana,
            "fecha_programada": fecha(2026, 11, 7, 9, 0),
            "personal_asignado": asignado(diana),
            "actividades_realizadas": ["Riego de orquídeas", "Poda de hojas secas", "Abonado de helechos"],
            "observaciones": ["Las orquídeas requieren cambio de sustrato en la próxima visita."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Abono orgánico", 3), insumo("Fertilizante NPK 10-30-10", 2)],
        },
        {
            "propiedad_id": casa_ana,
            "contrato_id": contrato_ana,
            "fecha_programada": fecha(2026, 11, 21, 9, 0),
            "personal_asignado": asignado(diana),
            "actividades_realizadas": ["Cambio de sustrato de orquídeas"],
            "observaciones": ["Visita programada con insumos por definir."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": casa_ana,
            "contrato_id": contrato_ana,
            "fecha_programada": fecha(2026, 11, 9, 15, 0),
            "personal_asignado": asignado(diana),
            "actividades_realizadas": ["Visita cancelada por solicitud del cliente"],
            "observaciones": ["El cliente reprogramará la visita."],
            "estado": "Cancelada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": hotel_norte,
            "contrato_id": contrato_hotel,
            "fecha_programada": fecha(2026, 11, 2, 6, 30),
            "personal_asignado": asignado(carlos_r, felipe, sofia),
            "actividades_realizadas": ["Poda de palmas", "Adecuación de jardín interior", "Mantenimiento de riego"],
            "observaciones": ["Se ajustó la programación del riego automático."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Fertilizante NPK 10-30-10", 6), insumo("Tierra abonada", 8), insumo("Fungicida a base de cobre", 4), insumo("Semilla de césped San Agustín", 10)],
        },
        {
            "propiedad_id": hotel_norte,
            "contrato_id": contrato_hotel,
            "fecha_programada": fecha(2026, 11, 16, 6, 30),
            "personal_asignado": asignado(felipe, carlos_r),
            "actividades_realizadas": ["Revisión de sistema de riego y poda de aves del paraíso"],
            "observaciones": ["Visita de mantenimiento preventivo."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": casa_esperanza,
            "contrato_id": contrato_camila,
            "fecha_programada": fecha(2026, 11, 8, 8, 0),
            "personal_asignado": asignado(lucia, diana),
            "actividades_realizadas": ["Poda de limoneros", "Siembra de hortensias", "Aplicación de humus"],
            "observaciones": ["Se amplió la zona de siembra junto al camino."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Abono orgánico", 6), insumo("Humus de lombriz", 10), insumo("Acondicionador de suelo", 5)],
        },
        {
            "propiedad_id": casa_esperanza,
            "contrato_id": contrato_camila,
            "fecha_programada": fecha(2026, 11, 22, 8, 0),
            "personal_asignado": asignado(lucia),
            "actividades_realizadas": ["Seguimiento de siembra y revisión de rosales"],
            "observaciones": ["Evaluar prendimiento de las nuevas hortensias."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": parque_cedros,
            "contrato_id": contrato_urbanizacion,
            "fecha_programada": fecha(2026, 11, 4, 7, 0),
            "personal_asignado": asignado(carlos_r, andres, sofia, felipe),
            "actividades_realizadas": ["Corte de césped", "Fertilización de zonas verdes", "Control de plagas en senderos"],
            "observaciones": ["Se recomienda programar resiembra en el sector oriental."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Abono orgánico", 6), insumo("Fertilizante NPK 10-30-10", 6), insumo("Fungicida a base de cobre", 4)],
        },
        {
            "propiedad_id": parque_cedros,
            "contrato_id": contrato_urbanizacion,
            "fecha_programada": fecha(2026, 11, 20, 7, 0),
            "personal_asignado": asignado(andres, carlos_r),
            "actividades_realizadas": ["Monitoreo fitosanitario de robles"],
            "observaciones": ["Revisar presencia de insectos en la zona boscosa."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": parque_empresarial,
            "contrato_id": contrato_parque_empresarial,
            "fecha_programada": fecha(2026, 11, 11, 8, 0),
            "personal_asignado": asignado(valentina, julian),
            "actividades_realizadas": ["Trazado de jardineras", "Preparación del terreno"],
            "observaciones": ["Se requiere nivelar el terreno antes de sembrar."],
            "estado": "En proceso",
            "insumos_utilizados": [insumo("Tierra abonada", 8)],
        },
        {
            "propiedad_id": oficina_301,
            "contrato_id": contrato_oficina,
            "fecha_programada": fecha(2026, 11, 9, 12, 0),
            "personal_asignado": asignado(diana),
            "actividades_realizadas": ["Visita cancelada por remodelación de la oficina"],
            "observaciones": ["Reprogramar cuando finalicen las obras."],
            "estado": "Cancelada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": apartamento_poblado,
            "contrato_id": contrato_jorge,
            "fecha_programada": fecha(2026, 8, 20, 10, 0),
            "personal_asignado": asignado(mauricio),
            "actividades_realizadas": ["Riego de suculentas", "Limpieza de balcón"],
            "observaciones": ["Servicio finalizado según lo pactado."],
            "estado": "Finalizada",
            "insumos_utilizados": [],
        },
    ]

    visitas_mantenimiento.insert_many(datos_visitas)

    crear_indices()

    print("\nDatos de demostración cargados correctamente:")
    print(f"  Clientes:               {clientes.count_documents({})}")
    print(f"  Propiedades:            {propiedades.count_documents({})}")
    print(f"  Contratos:              {servicios_contratos.count_documents({})}")
    print(f"  Personal:               {personal.count_documents({})}")
    print(f"  Visitas de mantenimiento:{visitas_mantenimiento.count_documents({})}")
    print(f"  Insumos:                {insumos.count_documents({})}")
    print(f"  Base de datos:          {db.name}")


if __name__ == "__main__":
    sembrar()
