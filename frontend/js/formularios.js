/* ============================================================
   VerdeVivo · Formularios de creación y edición
   ============================================================ */
(function () {
  "use strict";
  const V = window.Verde;
  const { escapar, abrirModal, cerrarModal, toast } = V;

  /* ------------------------- Utilidades de formulario ------------------------- */
  async function pedir(ruta) {
    const r = await V.api.get(ruta);
    return (r && r.datos) || [];
  }

  function opciones(lista, seleccionado, etiqueta, valor = (x) => x._id, extra = "") {
    return lista
      .map((item) => {
        const v = valor(item);
        const sel = String(v) === String(seleccionado || "") ? " selected" : "";
        return `<option value="${escapar(v)}"${sel}>${escapar(etiqueta(item))}${extra}</option>`;
      })
      .join("");
  }

  function campo({ id, etiqueta, tipo = "text", valor = "", req = false, full = false, ayuda = "", attrs = "", placeholder = "" }) {
    return `
      <label class="campo ${full ? "full" : ""}" for="${id}">
        <span>${escapar(etiqueta)} ${req ? '<span class="req">*</span>' : ""}</span>
        <input id="${id}" name="${id}" type="${tipo}" value="${escapar(valor)}"
               placeholder="${escapar(placeholder)}" ${req ? "required" : ""} ${attrs} />
        ${ayuda ? `<span class="ayuda">${escapar(ayuda)}</span>` : ""}
      </label>`;
  }

  function selector({ id, etiqueta, contenido, req = false, full = false, ayuda = "", attrs = "" }) {
    return `
      <label class="campo ${full ? "full" : ""}" for="${id}">
        <span>${escapar(etiqueta)} ${req ? '<span class="req">*</span>' : ""}</span>
        <select id="${id}" name="${id}" ${req ? "required" : ""} ${attrs}>${contenido}</select>
        ${ayuda ? `<span class="ayuda">${escapar(ayuda)}</span>` : ""}
      </label>`;
  }

  function area({ id, etiqueta, valor = "", full = true, filas = 3, ayuda = "", placeholder = "" }) {
    return `
      <label class="campo ${full ? "full" : ""}" for="${id}">
        <span>${escapar(etiqueta)}</span>
        <textarea id="${id}" name="${id}" rows="${filas}" placeholder="${escapar(placeholder)}">${escapar(valor)}</textarea>
        ${ayuda ? `<span class="ayuda">${escapar(ayuda)}</span>` : ""}
      </label>`;
  }

  function pieFormulario(etiquetaGuardar = "Guardar registro") {
    return `
      <button class="btn btn-ghost" type="button" id="btn-cancelar">Cancelar</button>
      <button class="btn btn-primario" type="submit" id="btn-guardar">
        <svg viewBox="0 0 24 24"><path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        ${escapar(etiquetaGuardar)}
      </button>`;
  }

  function conectarCierre() {
    const cancelar = document.getElementById("btn-cancelar");
    if (cancelar) cancelar.addEventListener("click", cerrarModal);
  }

  function mostrarError(mensaje) {
    const caja = document.getElementById("form-error");
    if (!caja) { toast(mensaje, "error"); return; }
    caja.textContent = mensaje;
    caja.classList.add("visible");
    caja.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function limpiarError() {
    const caja = document.getElementById("form-error");
    if (caja) { caja.textContent = ""; caja.classList.remove("visible"); }
  }

  async function enviar(url, metodo, cuerpo, alGuardar) {
    const boton = document.getElementById("btn-guardar");
    limpiarError();
    if (boton) { boton.disabled = true; boton.dataset.texto = boton.innerHTML; boton.textContent = "Guardando…"; }
    try {
      const respuesta = metodo === "POST" ? await V.api.post(url, cuerpo) : await V.api.put(url, cuerpo);
      toast((respuesta && respuesta.mensaje) || "Registro guardado correctamente.");
      cerrarModal();
      if (alGuardar) await alGuardar();
    } catch (error) {
      mostrarError(error.message);
      toast(error.message, "error");
    } finally {
      if (boton) { boton.disabled = false; boton.innerHTML = boton.dataset.texto || "Guardar"; }
    }
  }

  /* ------------------------- CLIENTES ------------------------- */
  function formularioCliente(registro, alGuardar) {
    const r = registro || {};
    abrirModal({
      titulo: registro ? "Editar cliente" : "Nuevo cliente",
      subtitulo: registro ? "Actualice los datos del cliente" : "Registre una persona o empresa en el sistema",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${campo({ id: "nombre", etiqueta: "Nombre o razón social", valor: r.nombre || "", req: true, full: true, placeholder: "Ej. Laura Martínez" })}
            ${campo({ id: "documento", etiqueta: "Documento (6 a 15 dígitos)", valor: r.documento || "", req: true, attrs: 'inputmode="numeric"' })}
            ${campo({ id: "telefono", etiqueta: "Teléfono", valor: r.telefono || "", req: true, placeholder: "3001234567" })}
            ${campo({ id: "correo", etiqueta: "Correo electrónico", valor: r.correo || "", req: true, tipo: "email" })}
            ${selector({
              id: "estado", etiqueta: "Estado", req: true,
              contenido: opciones(["Activo", "Inactivo"].map((e) => ({ _id: e })), r.estado || "Activo", (x) => x._id),
            })}
            ${campo({ id: "direccion", etiqueta: "Dirección", valor: r.direccion || "", req: true, full: true })}
          </div>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Registrar cliente"),
    });

    conectarCierre();
    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const cuerpo = {
        nombre: document.getElementById("nombre").value.trim(),
        documento: document.getElementById("documento").value.trim(),
        telefono: document.getElementById("telefono").value.trim(),
        correo: document.getElementById("correo").value.trim(),
        direccion: document.getElementById("direccion").value.trim(),
        estado: document.getElementById("estado").value,
      };
      enviar(registro ? `/clientes/${registro._id}` : "/clientes", registro ? "PUT" : "POST", cuerpo, alGuardar);
    });
  }

  /* ------------------------- PROPIEDADES ------------------------- */
  async function formularioPropiedad(registro, alGuardar) {
    const r = registro || {};
    let clientes = [];
    try { clientes = await pedir("/clientes"); } catch (e) { toast(e.message, "error"); return; }

    abrirModal({
      titulo: registro ? "Editar propiedad" : "Nueva propiedad",
      subtitulo: "Datos del predio y especies botánicas registradas",
      ancho: "modal-lg",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${selector({
              id: "cliente_id", etiqueta: "Cliente propietario", req: true, full: true,
              contenido: `<option value="">Seleccione un cliente…</option>` +
                opciones(clientes, r.cliente_id, (c) => `${c.nombre} · ${c.documento}`),
            })}
            ${campo({ id: "nombre", etiqueta: "Nombre de la propiedad", valor: r.nombre || "", req: true })}
            ${campo({ id: "ciudad", etiqueta: "Ciudad", valor: r.ciudad || "", req: true })}
            ${campo({ id: "direccion", etiqueta: "Dirección", valor: r.direccion || "", req: true })}
            ${campo({ id: "area_m2", etiqueta: "Área (m²)", valor: r.area_m2 ?? "", req: true, tipo: "number", attrs: 'min="0.01" step="0.01"' })}
            ${selector({
              id: "tipo_propiedad", etiqueta: "Tipo de propiedad", req: true,
              contenido: `<option value="">Seleccione…</option>` +
                opciones(["Casa", "Finca", "Apartamento", "Oficina", "Conjunto residencial", "Parque"].map((t) => ({ _id: t })), r.tipo_propiedad, (x) => x._id),
            })}
          </div>

          <fieldset class="bloque">
            <legend>Especies botánicas (documento embebido)</legend>
            <div class="repetidor" id="lista-especies"></div>
            <button type="button" class="btn-agregar" id="agregar-especie" style="margin-top:10px">
              ${V.iconos.mas} Agregar especie
            </button>
          </fieldset>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Registrar propiedad"),
    });

    conectarCierre();
    const contenedor = document.getElementById("lista-especies");

    function filaEspecie(datos = {}) {
      const div = document.createElement("div");
      div.className = "repetidor-fila especies";
      div.innerHTML = `
        <div class="mini"><span>Nombre común</span><input data-campo="nombre_comun" value="${escapar(datos.nombre_comun || "")}" placeholder="Rosa" /></div>
        <div class="mini"><span>Nombre científico</span><input data-campo="nombre_cientifico" value="${escapar(datos.nombre_cientifico || "")}" placeholder="Rosa spp." /></div>
        <div class="mini"><span>Cantidad</span><input data-campo="cantidad" type="number" min="1" step="1" value="${escapar(datos.cantidad ?? 1)}" /></div>
        <div class="mini"><span>Ubicación</span><input data-campo="ubicacion" value="${escapar(datos.ubicacion || "")}" placeholder="Jardín delantero" /></div>
        <div class="mini"><span>Necesidades de cuidado</span><input data-campo="necesidades_cuidado" value="${escapar(datos.necesidades_cuidado || "")}" placeholder="Riego y poda" /></div>
        <button type="button" class="btn-quitar" title="Quitar especie">${V.iconos.eliminar}</button>`;
      div.querySelector(".btn-quitar").addEventListener("click", () => div.remove());
      contenedor.appendChild(div);
    }

    (r.especies || []).forEach(filaEspecie);
    document.getElementById("agregar-especie").addEventListener("click", () => filaEspecie());

    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const especies = [];
      contenedor.querySelectorAll(".repetidor-fila").forEach((fila) => {
        const valor = (c) => fila.querySelector(`[data-campo="${c}"]`).value.trim();
        const nombre_comun = valor("nombre_comun");
        if (!nombre_comun) return;
        especies.push({
          nombre_comun,
          nombre_cientifico: valor("nombre_cientifico"),
          cantidad: Number(valor("cantidad") || 0),
          ubicacion: valor("ubicacion"),
          necesidades_cuidado: valor("necesidades_cuidado"),
        });
      });

      const cuerpo = {
        cliente_id: document.getElementById("cliente_id").value,
        nombre: document.getElementById("nombre").value.trim(),
        ciudad: document.getElementById("ciudad").value.trim(),
        direccion: document.getElementById("direccion").value.trim(),
        tipo_propiedad: document.getElementById("tipo_propiedad").value,
        area_m2: Number(document.getElementById("area_m2").value),
        especies,
      };
      enviar(registro ? `/propiedades/${registro._id}` : "/propiedades", registro ? "PUT" : "POST", cuerpo, alGuardar);
    });
  }

  /* ------------------------- CONTRATOS ------------------------- */
  async function formularioContrato(registro, alGuardar) {
    const r = registro || {};
    let clientes = [];
    try { clientes = await pedir("/clientes"); } catch (e) { toast(e.message, "error"); return; }

    abrirModal({
      titulo: registro ? "Editar contrato" : "Nuevo contrato",
      subtitulo: "Servicios contratados, vigencia y valor acordado",
      ancho: "modal-lg",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${selector({
              id: "cliente_id", etiqueta: "Cliente", req: true, full: true,
              contenido: `<option value="">Seleccione un cliente…</option>` +
                opciones(clientes, r.cliente_id, (c) => `${c.nombre} · ${c.documento}`),
            })}
            ${campo({ id: "fecha_inicio", etiqueta: "Fecha de inicio", valor: V.paraInputFecha(r.fecha_inicio, false), req: true, tipo: "date" })}
            ${campo({ id: "fecha_fin", etiqueta: "Fecha de finalización", valor: V.paraInputFecha(r.fecha_fin, false), req: true, tipo: "date" })}
            ${selector({
              id: "estado", etiqueta: "Estado del contrato", req: true,
              contenido: opciones(["Activo", "Suspendido", "Finalizado", "Vencido"].map((e) => ({ _id: e })), r.estado || "Activo", (x) => x._id),
            })}
          </div>

          <fieldset class="bloque">
            <legend>Servicios del contrato (arreglo embebido)</legend>
            <div class="repetidor" id="lista-servicios"></div>
            <button type="button" class="btn-agregar" id="agregar-servicio" style="margin-top:10px">
              ${V.iconos.mas} Agregar servicio
            </button>
            <div class="total-live"><span>Valor total del contrato (calculado)</span><b id="total-contrato">$0</b></div>
          </fieldset>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Registrar contrato"),
    });

    conectarCierre();
    const contenedor = document.getElementById("lista-servicios");
    const totalEl = document.getElementById("total-contrato");

    function recalcular() {
      let total = 0;
      contenedor.querySelectorAll('[data-campo="precio_acordado"]').forEach((i) => {
        total += Number(i.value || 0);
      });
      totalEl.textContent = V.moneda(total);
    }

    function filaServicio(datos = {}) {
      const div = document.createElement("div");
      div.className = "repetidor-fila servicios";
      div.innerHTML = `
        <div class="mini"><span>Nombre del servicio</span><input data-campo="nombre" value="${escapar(datos.nombre || "")}" placeholder="Poda de setos" /></div>
        <div class="mini"><span>Descripción</span><input data-campo="descripcion" value="${escapar(datos.descripcion || "")}" placeholder="Detalle del servicio" /></div>
        <div class="mini"><span>Precio acordado</span><input data-campo="precio_acordado" type="number" min="1" step="1" value="${escapar(datos.precio_acordado ?? "")}" placeholder="0" /></div>
        <button type="button" class="btn-quitar" title="Quitar servicio">${V.iconos.eliminar}</button>`;
      div.querySelector('[data-campo="precio_acordado"]').addEventListener("input", recalcular);
      div.querySelector(".btn-quitar").addEventListener("click", () => { div.remove(); recalcular(); });
      contenedor.appendChild(div);
    }

    (r.servicios || []).forEach(filaServicio);
    if (!(r.servicios || []).length) filaServicio();
    document.getElementById("agregar-servicio").addEventListener("click", () => filaServicio());
    recalcular();

    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const servicios = [];
      contenedor.querySelectorAll(".repetidor-fila").forEach((fila) => {
        const valor = (c) => fila.querySelector(`[data-campo="${c}"]`).value.trim();
        if (!valor("nombre")) return;
        servicios.push({
          nombre: valor("nombre"),
          descripcion: valor("descripcion"),
          precio_acordado: Number(valor("precio_acordado") || 0),
        });
      });
      const cuerpo = {
        cliente_id: document.getElementById("cliente_id").value,
        servicios,
        fecha_inicio: document.getElementById("fecha_inicio").value,
        fecha_fin: document.getElementById("fecha_fin").value,
        estado: document.getElementById("estado").value,
      };
      enviar(registro ? `/servicios_contratos/${registro._id}` : "/servicios_contratos", registro ? "PUT" : "POST", cuerpo, alGuardar);
    });
  }

  /* ------------------------- PERSONAL ------------------------- */
  function formularioPersonal(registro, alGuardar) {
    const r = registro || {};
    abrirModal({
      titulo: registro ? "Editar trabajador" : "Nuevo trabajador",
      subtitulo: "Datos del personal técnico y operativo",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${campo({ id: "nombre", etiqueta: "Nombre completo", valor: r.nombre || "", req: true, full: true })}
            ${campo({ id: "documento", etiqueta: "Documento (6 a 15 dígitos)", valor: r.documento || "", req: true, attrs: 'inputmode="numeric"' })}
            ${campo({ id: "telefono", etiqueta: "Teléfono", valor: r.telefono || "", req: true })}
            ${campo({ id: "correo", etiqueta: "Correo electrónico", valor: r.correo || "", req: true, tipo: "email" })}
            ${selector({
              id: "cargo", etiqueta: "Cargo", req: true,
              contenido: `<option value="">Seleccione…</option>` +
                opciones(["Jardinero", "Paisajista", "Especialista botánico", "Supervisor", "Auxiliar de jardinería"].map((c) => ({ _id: c })), r.cargo, (x) => x._id),
            })}
            ${campo({ id: "salario", etiqueta: "Salario (COP)", valor: r.salario ?? "", tipo: "number", attrs: 'min="0" step="1000"', ayuda: "Opcional" })}
            ${selector({
              id: "estado", etiqueta: "Estado", req: true,
              contenido: opciones(["Activo", "Inactivo"].map((e) => ({ _id: e })), r.estado || "Activo", (x) => x._id),
            })}
            ${campo({
              id: "especialidades", etiqueta: "Especialidades", full: true,
              valor: (r.especialidades || []).join(", "),
              ayuda: "Separe varias especialidades con comas. Ej. Poda, Riego, Control de plagas",
            })}
          </div>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Registrar trabajador"),
    });

    conectarCierre();
    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const salarioTexto = document.getElementById("salario").value;
      const cuerpo = {
        nombre: document.getElementById("nombre").value.trim(),
        documento: document.getElementById("documento").value.trim(),
        telefono: document.getElementById("telefono").value.trim(),
        correo: document.getElementById("correo").value.trim(),
        cargo: document.getElementById("cargo").value,
        estado: document.getElementById("estado").value,
        especialidades: document.getElementById("especialidades").value
          .split(",").map((x) => x.trim()).filter(Boolean),
      };
      if (salarioTexto !== "") cuerpo.salario = Number(salarioTexto);
      enviar(registro ? `/personal/${registro._id}` : "/personal", registro ? "PUT" : "POST", cuerpo, alGuardar);
    });
  }

  /* ------------------------- INSUMOS ------------------------- */
  function formularioInsumo(registro, alGuardar) {
    const r = registro || {};
    abrirModal({
      titulo: registro ? "Editar insumo" : "Nuevo insumo",
      subtitulo: "Inventario de insumos y stock mínimo de seguridad",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${campo({ id: "nombre", etiqueta: "Nombre del insumo", valor: r.nombre || "", req: true, full: true, placeholder: "Ej. Fertilizante NPK" })}
            ${campo({ id: "descripcion", etiqueta: "Descripción", valor: r.descripcion || "", full: true })}
            ${selector({
              id: "unidad_medida", etiqueta: "Unidad de medida", req: true,
              contenido: `<option value="">Seleccione…</option>` +
                opciones(["Kilogramos", "Litros", "Unidades", "Bultos", "Metros", "Mililitros"].map((u) => ({ _id: u })), r.unidad_medida, (x) => x._id),
            })}
            ${campo({ id: "existencias", etiqueta: "Existencias actuales", valor: r.existencias ?? 0, req: true, tipo: "number", attrs: 'min="0" step="1"' })}
            ${campo({ id: "stock_minimo", etiqueta: "Stock mínimo", valor: r.stock_minimo ?? 0, req: true, tipo: "number", attrs: 'min="0" step="1"' })}
            <label class="campo" for="estado-calculado">
              <span>Estado del inventario (calculado)</span>
              <input id="estado-calculado" value="${escapar(r.estado || "Se calcula automáticamente")}" disabled />
              <span class="ayuda">Se deriva de las existencias y el stock mínimo.</span>
            </label>
          </div>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Registrar insumo"),
    });

    conectarCierre();
    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const cuerpo = {
        nombre: document.getElementById("nombre").value.trim(),
        descripcion: document.getElementById("descripcion").value.trim(),
        unidad_medida: document.getElementById("unidad_medida").value,
        existencias: Number(document.getElementById("existencias").value),
        stock_minimo: Number(document.getElementById("stock_minimo").value),
      };
      enviar(registro ? `/insumos/${registro._id}` : "/insumos", registro ? "PUT" : "POST", cuerpo, alGuardar);
    });
  }

  /* ------------------------- VISITAS ------------------------- */
  async function formularioVisita(registro, alGuardar) {
    const r = registro || {};
    let propiedades = [], contratos = [], personal = [], insumos = [];
    try {
      [propiedades, contratos, personal, insumos] = await Promise.all([
        pedir("/propiedades"), pedir("/servicios_contratos"), pedir("/personal"), pedir("/insumos"),
      ]);
    } catch (e) {
      toast(e.message, "error");
      return;
    }

    const estadosSinConsumo = ["Programada", "Cancelada"];

    abrirModal({
      titulo: registro ? "Editar visita de mantenimiento" : "Nueva visita de mantenimiento",
      subtitulo: "Programación, personal asignado y consumo de insumos",
      ancho: "modal-lg",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${selector({
              id: "propiedad_id", etiqueta: "Propiedad", req: true,
              contenido: `<option value="">Seleccione una propiedad…</option>` +
                opciones(propiedades, r.propiedad_id, (p) => `${p.nombre} · ${p.cliente_nombre || ""}`),
            })}
            ${selector({
              id: "contrato_id", etiqueta: "Contrato asociado", req: true,
              contenido: `<option value="">Seleccione un contrato…</option>` +
                opciones(contratos, r.contrato_id, (c) => `${c.cliente_nombre || "Cliente"} · ${c.estado} · ${V.fechaCorta(c.fecha_inicio)} a ${V.fechaCorta(c.fecha_fin)}`),
              ayuda: "El contrato debe estar activo y pertenecer al mismo cliente de la propiedad.",
            })}
            ${campo({ id: "fecha_programada", etiqueta: "Fecha y hora programada", valor: V.paraInputFecha(r.fecha_programada, true), req: true, tipo: "datetime-local" })}
            ${selector({
              id: "estado", etiqueta: "Estado de la visita", req: true,
              contenido: opciones(["Programada", "En proceso", "Finalizada", "Cancelada"].map((e) => ({ _id: e })), r.estado || "Programada", (x) => x._id),
            })}
          </div>

          <fieldset class="bloque">
            <legend>Personal asignado (referencia)</legend>
            <div class="checks-grid" id="lista-personal">
              ${personal.map((p) => {
                const asignado = (r.personal_asignado || []).some((x) => String(x.personal_id) === String(p._id));
                const inactivo = p.estado !== "Activo";
                return `<label class="check-item ${inactivo ? "inactivo" : ""}">
                  <input type="checkbox" value="${escapar(p._id)}" ${asignado ? "checked" : ""} ${inactivo ? "disabled" : ""} />
                  <span>${escapar(p.nombre)}</span><small>${escapar(p.cargo)}${inactivo ? " · Inactivo" : ""}</small>
                </label>`;
              }).join("") || '<small style="color:#87948b">No hay trabajadores registrados.</small>'}
            </div>
          </fieldset>

          <fieldset class="bloque" id="bloque-insumos">
            <legend>Insumos utilizados (control de inventario)</legend>
            <div class="repetidor" id="lista-insumos"></div>
            <button type="button" class="btn-agregar" id="agregar-insumo" style="margin-top:10px">
              ${V.iconos.mas} Agregar insumo
            </button>
            <div class="ayuda" style="margin-top:8px;font-size:11px;color:#87948b">
              El consumo solo se permite cuando la visita está <b>En proceso</b> o <b>Finalizada</b>.
              El stock se descuenta automáticamente.
            </div>
          </fieldset>

          <fieldset class="bloque">
            <legend>Actividades y observaciones</legend>
            <div class="form-grid">
              ${area({ id: "actividades", etiqueta: "Actividades realizadas (una por línea)", valor: (r.actividades_realizadas || []).join("\n"), filas: 3, full: true })}
              ${area({ id: "observaciones", etiqueta: "Observaciones (una por línea)", valor: (r.observaciones || []).join("\n"), filas: 2, full: true })}
            </div>
          </fieldset>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Programar visita"),
    });

    conectarCierre();

    const selPropiedad = document.getElementById("propiedad_id");
    const selContrato = document.getElementById("contrato_id");
    const selEstado = document.getElementById("estado");
    const bloqueInsumos = document.getElementById("bloque-insumos");
    const contenedor = document.getElementById("lista-insumos");
    const mapaPropiedades = Object.fromEntries(propiedades.map((p) => [p._id, p]));

    /* Filtra contratos por cliente de la propiedad seleccionada */
    function filtrarContratos() {
      const propiedad = mapaPropiedades[selPropiedad.value];
      const clienteId = propiedad ? propiedad.cliente_id : null;
      const seleccionado = selContrato.value || r.contrato_id || "";
      const disponibles = contratos.filter((c) => !clienteId || c.cliente_id === clienteId);
      selContrato.innerHTML = `<option value="">Seleccione un contrato…</option>` +
        opciones(disponibles, seleccionado, (c) => `${c.estado} · ${V.fechaCorta(c.fecha_inicio)} a ${V.fechaCorta(c.fecha_fin)} · ${V.moneda(c.valor_total)}`);
    }
    filtrarContratos();
    selPropiedad.addEventListener("change", () => { selContrato.value = ""; filtrarContratos(); });

    /* Insumos dinámicos */
    function filaInsumo(datos = {}) {
      const div = document.createElement("div");
      div.className = "repetidor-fila insumos";
      const seleccionado = datos.insumo_id || "";
      div.innerHTML = `
        <div class="mini"><span>Insumo</span>
          <select data-campo="insumo_id">
            <option value="">Seleccione…</option>
            ${insumos.map((i) => `<option value="${escapar(i._id)}" ${String(i._id) === String(seleccionado) ? "selected" : ""}>${escapar(i.nombre)} (${V.numero(i.existencias)} ${escapar(i.unidad_medida)})</option>`).join("")}
          </select>
        </div>
        <div class="mini"><span>Cantidad</span><input data-campo="cantidad" type="number" min="1" step="1" value="${escapar(datos.cantidad ?? 1)}" /></div>
        <div class="mini"><span>Unidad</span><input value="${escapar(datos.unidad_medida || "")}" disabled /></div>
        <button type="button" class="btn-quitar" title="Quitar insumo">${V.iconos.eliminar}</button>`;
      const select = div.querySelector('[data-campo="insumo_id"]');
      const unidad = div.querySelectorAll("input")[1];
      select.addEventListener("change", () => {
        const item = insumos.find((i) => i._id === select.value);
        unidad.value = item ? item.unidad_medida : "";
      });
      div.querySelector(".btn-quitar").addEventListener("click", () => div.remove());
      contenedor.appendChild(div);
    }

    (r.insumos_utilizados || []).forEach(filaInsumo);
    document.getElementById("agregar-insumo").addEventListener("click", () => filaInsumo());

    function aplicarEstado() {
      const sinConsumo = estadosSinConsumo.includes(selEstado.value);
      bloqueInsumos.style.display = sinConsumo ? "none" : "";
      if (sinConsumo) contenedor.innerHTML = "";
    }
    aplicarEstado();
    selEstado.addEventListener("change", aplicarEstado);

    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const personalAsignado = Array.from(
        document.querySelectorAll("#lista-personal input:checked")
      ).map((i) => i.value);

      const insumosUtilizados = [];
      if (!estadosSinConsumo.includes(selEstado.value)) {
        contenedor.querySelectorAll(".repetidor-fila").forEach((fila) => {
          const insumo_id = fila.querySelector('[data-campo="insumo_id"]').value;
          if (!insumo_id) return;
          insumosUtilizados.push({
            insumo_id,
            cantidad: Number(fila.querySelector('[data-campo="cantidad"]').value || 0),
          });
        });
      }

      const cuerpo = {
        propiedad_id: selPropiedad.value,
        contrato_id: selContrato.value,
        fecha_programada: document.getElementById("fecha_programada").value,
        estado: selEstado.value,
        personal_asignado: personalAsignado,
        insumos_utilizados: insumosUtilizados,
        actividades_realizadas: document.getElementById("actividades").value.split("\n").map((x) => x.trim()).filter(Boolean),
        observaciones: document.getElementById("observaciones").value.split("\n").map((x) => x.trim()).filter(Boolean),
      };

      /* En edición se envían solo los campos modificados para no revalidar
         relaciones históricas (contratos finalizados, personal inactivo, etc.). */
      let payload = cuerpo;
      if (registro) {
        payload = {};
        const original = {
          propiedad_id: registro.propiedad_id,
          contrato_id: registro.contrato_id,
          fecha_programada: registro.fecha_programada,
          estado: registro.estado,
          personal_asignado: (registro.personal_asignado || []).map((p) => p.personal_id),
          insumos_utilizados: (registro.insumos_utilizados || []).map((i) => ({ insumo_id: i.insumo_id, cantidad: i.cantidad })),
          actividades_realizadas: registro.actividades_realizadas || [],
          observaciones: registro.observaciones || [],
        };
        Object.keys(cuerpo).forEach((clave) => {
          if (clave === "fecha_programada") {
            if (V.paraInputFecha(original.fecha_programada, true) !== cuerpo.fecha_programada) payload[clave] = cuerpo[clave];
          } else if (JSON.stringify(original[clave]) !== JSON.stringify(cuerpo[clave])) {
            payload[clave] = cuerpo[clave];
          }
        });
        if (!Object.keys(payload).length) {
          toast("No hay cambios por guardar.", "info");
          return;
        }
      }

      enviar(registro ? `/visitas_mantenimiento/${registro._id}` : "/visitas_mantenimiento", registro ? "PUT" : "POST", payload, alGuardar);
    });
  }

  window.Verde.formularios = {
    clientes: formularioCliente,
    propiedades: formularioPropiedad,
    contratos: formularioContrato,
    personal: formularioPersonal,
    insumos: formularioInsumo,
    visitas: formularioVisita,
  };
})();
