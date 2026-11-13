/* ============================================================
   VerdeVivo · Vistas de la aplicación
   ============================================================ */
(function () {
  "use strict";
  const V = window.Verde;
  const { escapar, moneda, numero, fecha, fechaCorta, badge, chip, toast, confirmar } = V;

  const graficos = [];
  function destruirGraficos() {
    while (graficos.length) {
      const g = graficos.pop();
      try { g.destroy(); } catch (_) { /* ignorar */ }
    }
  }

  function registrarGrafico(grafico) {
    if (grafico) graficos.push(grafico);
  }

  function barraBusqueda(placeholder) {
    return `<div class="search-box">${V.iconos.buscar}<input type="search" id="filtro-q" placeholder="${escapar(placeholder)}" autocomplete="off" /></div>`;
  }

  function selectFiltro(id, etiqueta, valores, actual = "") {
    return `<select id="${id}" aria-label="${escapar(etiqueta)}">
      <option value="">${escapar(etiqueta)}</option>
      ${valores.map((v) => `<option value="${escapar(v)}" ${v === actual ? "selected" : ""}>${escapar(v)}</option>`).join("")}
    </select>`;
  }

  function tabla(cabeceras, filas, vacio) {
    if (!filas.length) return vacio;
    return `<div class="tabla-wrap"><table class="tabla">
      <thead><tr>${cabeceras.map((c) => `<th>${c}</th>`).join("")}</tr></thead>
      <tbody>${filas.join("")}</tbody>
    </table></div>`;
  }

  function acciones(id, opciones = {}) {
    return `<div class="celda-acciones">
      ${opciones.ver ? `<button class="btn-icon" data-accion="ver" data-id="${id}" title="Ver detalle">${V.iconos.ver}</button>` : ""}
      ${opciones.editar !== false ? `<button class="btn-icon" data-accion="editar" data-id="${id}" title="Editar">${V.iconos.editar}</button>` : ""}
      <button class="btn-icon peligro" data-accion="eliminar" data-id="${id}" title="Eliminar">${V.iconos.eliminar}</button>
    </div>`;
  }

  function debounce(fn, ms = 320) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  }

  async function eliminarRegistro(ruta, nombre, alTerminar) {
    const ok = await confirmar({
      titulo: "Eliminar registro",
      texto: `¿Está seguro de eliminar ${nombre}? Esta acción no se puede deshacer.`,
      etiqueta: "Sí, eliminar",
    });
    if (!ok) return;
    try {
      const r = await V.api.del(ruta);
      toast((r && r.mensaje) || "Registro eliminado correctamente.");
      await alTerminar();
    } catch (error) {
      toast(error.message, "error");
    }
  }

  /* ============================================================
     PANEL GENERAL
     ============================================================ */
  async function panel(cont) {
    V.cargando(cont);
    let k;
    try {
      const r = await V.api.get("/analitica/kpis");
      k = r.datos;
    } catch (error) {
      cont.innerHTML = `<div class="card">${V.vacio("⚠️", "No fue posible cargar el tablero", error.message)}</div>`;
      return;
    }

    const porEstado = k.visitas_por_estado || {};
    const proximas = k.proximas_visitas || [];
    const criticos = k.insumos_criticos || [];

    cont.innerHTML = `
      <section class="kpi-grid">
        <article class="kpi">
          <div class="kpi-label">Clientes activos</div>
          <div class="kpi-valor">${numero(k.clientes_activos)}</div>
          <div class="kpi-detalle">de ${numero(k.clientes_total)} clientes registrados</div>
          <span class="kpi-icon">👥</span>
        </article>
        <article class="kpi">
          <div class="kpi-label">Propiedades gestionadas</div>
          <div class="kpi-valor">${numero(k.propiedades_total)}</div>
          <div class="kpi-detalle">${numero(k.area_total_m2)} m² de área total</div>
          <span class="kpi-icon">🌳</span>
        </article>
        <article class="kpi">
          <div class="kpi-label">Contratos activos</div>
          <div class="kpi-valor">${numero(k.contratos_activos)}</div>
          <div class="kpi-detalle">Cartera: ${moneda(k.valor_cartera)}</div>
          <span class="kpi-icon">📄</span>
        </article>
        <article class="kpi">
          <div class="kpi-label">Visitas registradas</div>
          <div class="kpi-valor">${numero(k.visitas_total)}</div>
          <div class="kpi-detalle">Cumplimiento: ${numero(k.tasa_cumplimiento, 1)}%</div>
          <span class="kpi-icon">🗓️</span>
        </article>
        <article class="kpi ${k.insumos_criticos_total ? "kpi-alerta" : ""}">
          <div class="kpi-label">Insumos críticos</div>
          <div class="kpi-valor">${numero(k.insumos_criticos_total)}</div>
          <div class="kpi-detalle">${k.insumo_mas_consumido ? "Más usado: " + escapar(k.insumo_mas_consumido.nombre) : "Sin consumos registrados"}</div>
          <span class="kpi-icon">🌱</span>
        </article>
        <article class="kpi">
          <div class="kpi-label">Personal activo</div>
          <div class="kpi-valor">${numero(k.personal_activo)}</div>
          <div class="kpi-detalle">de ${numero(k.personal_total)} trabajadores</div>
          <span class="kpi-icon">👷</span>
        </article>
      </section>

      <div class="dashboard-grid">
        <section class="card">
          <div class="card-head">
            <div>
              <h3>Distribución de visitas por estado</h3>
              <p>Seguimiento operativo de las visitas de mantenimiento</p>
            </div>
            <span class="chip">${numero(k.visitas_total)} visitas</span>
          </div>
          <div class="chart-box"><canvas id="grafico-estados"></canvas></div>
        </section>

        <section class="card">
          <div class="card-head">
            <div>
              <h3>Próximas visitas (7 días)</h3>
              <p>Programadas y en proceso</p>
            </div>
          </div>
          <div class="lista-simple">
            ${proximas.length ? proximas.map((v) => `
              <div class="lista-item">
                <span class="avatar">${escapar(V.iniciales(v.cliente_nombre))}</span>
                <div class="grow">
                  <strong>${escapar(v.propiedad_nombre)}</strong>
                  <small>${escapar(v.cliente_nombre)} · ${fecha(v.fecha_programada, true)}</small>
                </div>
                ${badge(v.estado)}
              </div>`).join("") : V.vacio("🌤️", "Sin visitas próximas", "No hay visitas programadas en los próximos 7 días.")}
          </div>
        </section>
      </div>

      <div class="dashboard-grid-2">
        <section class="card">
          <div class="card-head">
            <div>
              <h3>Insumos que requieren reposición</h3>
              <p>Existencias iguales o por debajo del stock mínimo</p>
            </div>
            <span class="chip ambar">${criticos.length} alertas</span>
          </div>
          <div class="lista-simple">
            ${criticos.length ? criticos.slice(0, 6).map((i) => `
              <div class="lista-item">
                <span class="avatar alerta">!</span>
                <div class="grow">
                  <strong>${escapar(i.nombre)}</strong>
                  <small>${numero(i.existencias)} ${escapar(i.unidad_medida)} disponibles · mínimo ${numero(i.stock_minimo)}</small>
                </div>
                ${badge(i.estado)}
              </div>`).join("") : V.vacio("✅", "Inventario saludable", "Ningún insumo está por debajo del stock mínimo.")}
          </div>
        </section>

        <section class="card">
          <div class="card-head">
            <div>
              <h3>Resumen de cartera</h3>
              <p>Contratos activos y valor promedio</p>
            </div>
          </div>
          <div class="card-pad">
            <div class="detalle-grid">
              <div class="detalle-campo"><small>Valor de cartera</small><strong>${moneda(k.valor_cartera)}</strong></div>
              <div class="detalle-campo"><small>Promedio por contrato</small><strong>${moneda(k.valor_promedio_contrato)}</strong></div>
              <div class="detalle-campo"><small>Área total gestionada</small><strong>${numero(k.area_total_m2)} m²</strong></div>
              <div class="detalle-campo"><small>Insumo más consumido</small><strong>${k.insumo_mas_consumido ? escapar(k.insumo_mas_consumido.nombre) + " · " + numero(k.insumo_mas_consumido.cantidad) : "—"}</strong></div>
            </div>
            <p class="seccion-titulo">Estado de las visitas</p>
            <div class="chips">
              ${Object.entries(porEstado).map(([estado, total]) => `<span class="chip">${escapar(estado)}: ${total}</span>`).join("") || '<span class="chip neutro">Sin datos</span>'}
            </div>
          </div>
        </section>
      </div>`;

    if (window.Chart && document.getElementById("grafico-estados")) {
      const etiquetas = Object.keys(porEstado);
      registrarGrafico(new Chart(document.getElementById("grafico-estados"), {
        type: "doughnut",
        data: {
          labels: etiquetas,
          datasets: [{
            data: etiquetas.map((e) => porEstado[e]),
            backgroundColor: ["#2b8150", "#c07a13", "#b7d94b", "#9aa79d", "#2a6f97"],
            borderWidth: 2,
            borderColor: "#fff",
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false, cutout: "62%",
          plugins: {
            legend: { position: "bottom", labels: { boxWidth: 9, boxHeight: 9, usePointStyle: true, font: { size: 11, family: "Manrope" } } },
          },
        },
      }));
    }
  }

  /* ============================================================
     CLIENTES
     ============================================================ */
  async function clientes(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar por nombre, documento, correo o dirección…")}
        ${selectFiltro("filtro-estado", "Todos los estados", ["Activo", "Inactivo"])}
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nuevo cliente</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const estado = document.getElementById("filtro-estado").value;
      if (q) params.set("q", q);
      if (estado) params.set("estado", estado);
      try {
        const r = await V.api.get("/clientes?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> registros`;
        contenedor.innerHTML = tabla(
          ["Cliente", "Documento", "Teléfono", "Correo", "Estado", ""],
          datos.map((c) => `
            <tr>
              <td><div class="principal">${escapar(c.nombre)}</div><div class="secundario">${escapar(c.direccion)}</div></td>
              <td>${escapar(c.documento)}</td>
              <td>${escapar(c.telefono)}</td>
              <td>${escapar(c.correo)}</td>
              <td>${badge(c.estado)}</td>
              <td>${acciones(c._id)}</td>
            </tr>`),
          V.vacio("👥", "No hay clientes", "Registre el primer cliente o ajuste los filtros de búsqueda.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar clientes", error.message);
      }
    }

    contenedor.addEventListener("click", async (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "editar") V.formularios.clientes(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/clientes/${registro._id}`, `al cliente "${registro.nombre}"`, cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.clientes(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-estado").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     PROPIEDADES
     ============================================================ */
  async function propiedades(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar por nombre, ciudad, dirección o especie…")}
        ${selectFiltro("filtro-tipo", "Todos los tipos", ["Casa", "Finca", "Apartamento", "Oficina", "Conjunto residencial", "Parque"])}
        <input type="search" id="filtro-ciudad" placeholder="Ciudad" style="max-width:150px" />
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nueva propiedad</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const tipo = document.getElementById("filtro-tipo").value;
      const ciudad = document.getElementById("filtro-ciudad").value.trim();
      if (q) params.set("q", q);
      if (tipo) params.set("tipo_propiedad", tipo);
      if (ciudad) params.set("ciudad", ciudad);
      try {
        const r = await V.api.get("/propiedades?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> propiedades`;
        contenedor.innerHTML = tabla(
          ["Propiedad", "Cliente", "Ciudad", "Tipo", "Área", "Especies", "Visitas", ""],
          datos.map((p) => `
            <tr>
              <td><div class="principal">${escapar(p.nombre)}</div><div class="secundario">${escapar(p.direccion)}</div></td>
              <td><div>${escapar(p.cliente_nombre)}</div><div class="secundario">${escapar(p.cliente_documento)}</div></td>
              <td>${escapar(p.ciudad)}</td>
              <td>${chip(p.tipo_propiedad, "neutro")}</td>
              <td class="num">${numero(p.area_m2)} m²</td>
              <td><span class="chip">${numero(p.total_especies)}</span></td>
              <td><span class="chip azul">${numero(p.total_visitas)}</span></td>
              <td>${acciones(p._id, { ver: true })}</td>
            </tr>`),
          V.vacio("🏡", "No hay propiedades", "Registre una propiedad o ajuste los filtros.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar propiedades", error.message);
      }
    }

    async function verDetalle(propiedad) {
      let historial = [];
      try {
        const r = await V.api.get(`/propiedades/${propiedad._id}/historial`);
        historial = r.datos || [];
      } catch (_) { /* historial opcional */ }

      V.abrirModal({
        titulo: propiedad.nombre,
        subtitulo: `${propiedad.tipo_propiedad} · ${propiedad.ciudad} · ${numero(propiedad.area_m2)} m²`,
        ancho: "modal-lg",
        cuerpo: `
          <div class="detalle-grid">
            <div class="detalle-campo"><small>Cliente</small><strong>${escapar(propiedad.cliente_nombre)}</strong></div>
            <div class="detalle-campo"><small>Documento</small><strong>${escapar(propiedad.cliente_documento || "—")}</strong></div>
            <div class="detalle-campo"><small>Dirección</small><strong>${escapar(propiedad.direccion)}</strong></div>
            <div class="detalle-campo"><small>Visitas registradas</small><strong>${numero(propiedad.total_visitas)}</strong></div>
          </div>
          <p class="seccion-titulo">Especies botánicas (${(propiedad.especies || []).length})</p>
          ${(propiedad.especies || []).length ? `<div class="tabla-wrap"><table class="tabla" style="min-width:520px">
            <thead><tr><th>Nombre común</th><th>Nombre científico</th><th>Cantidad</th><th>Ubicación</th><th>Cuidados</th></tr></thead>
            <tbody>${propiedad.especies.map((e) => `
              <tr><td class="principal">${escapar(e.nombre_comun)}</td><td><i>${escapar(e.nombre_cientifico)}</i></td>
              <td class="num">${numero(e.cantidad)}</td><td>${escapar(e.ubicacion)}</td><td class="secundario">${escapar(e.necesidades_cuidado)}</td></tr>`).join("")}
            </tbody></table></div>` : '<p class="secundario">Sin especies registradas.</p>'}
          <p class="seccion-titulo">Historial de mantenimiento (${historial.length})</p>
          ${historial.length ? `<div class="tabla-wrap"><table class="tabla" style="min-width:520px">
            <thead><tr><th>Fecha</th><th>Estado</th><th>Servicios del contrato</th><th>Actividades</th></tr></thead>
            <tbody>${historial.map((h) => `
              <tr><td>${fecha(h.fecha_programada, true)}</td><td>${badge(h.estado)}</td>
              <td><div class="chips">${(h.servicios_contratados || []).map((s) => chip(s)).join("") || "—"}</div></td>
              <td class="secundario">${(h.actividades_realizadas || []).join(" · ") || "—"}</td></tr>`).join("")}
            </tbody></table></div>` : '<p class="secundario">Esta propiedad aún no tiene visitas.</p>'}`,
        pie: `<button class="btn btn-ghost" type="button" id="btn-cancelar">Cerrar</button>`,
      });
      document.getElementById("btn-cancelar").addEventListener("click", V.cerrarModal);
    }

    contenedor.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "ver") verDetalle(registro);
      if (boton.dataset.accion === "editar") V.formularios.propiedades(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/propiedades/${registro._id}`, `la propiedad "${registro.nombre}"`, cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.propiedades(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-ciudad").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-tipo").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     CONTRATOS
     ============================================================ */
  async function contratos(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar por servicio o descripción…")}
        ${selectFiltro("filtro-estado", "Todos los estados", ["Activo", "Suspendido", "Finalizado", "Vencido"])}
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nuevo contrato</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const estado = document.getElementById("filtro-estado").value;
      if (q) params.set("q", q);
      if (estado) params.set("estado", estado);
      try {
        const r = await V.api.get("/servicios_contratos?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> contratos`;
        contenedor.innerHTML = tabla(
          ["Cliente", "Servicios", "Vigencia", "Valor total", "Estado", ""],
          datos.map((c) => {
            const servicios = c.servicios || [];
            return `<tr>
              <td><div class="principal">${escapar(c.cliente_nombre)}</div><div class="secundario">${escapar(c.cliente_documento)}</div></td>
              <td><div class="chips">
                ${servicios.slice(0, 2).map((s) => chip(s.nombre)).join("")}
                ${servicios.length > 2 ? chip(`+${servicios.length - 2}`, "neutro") : ""}
              </div></td>
              <td><div>${fechaCorta(c.fecha_inicio)}</div><div class="secundario">hasta ${fechaCorta(c.fecha_fin)}</div></td>
              <td class="num principal">${moneda(c.valor_total)}</td>
              <td>${badge(c.estado)}</td>
              <td>${acciones(c._id, { ver: true })}</td>
            </tr>`;
          }),
          V.vacio("📄", "No hay contratos", "Registre un contrato o ajuste los filtros.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar contratos", error.message);
      }
    }

    function verDetalle(contrato) {
      const servicios = contrato.servicios || [];
      V.abrirModal({
        titulo: "Contrato de " + contrato.cliente_nombre,
        subtitulo: `${contrato.estado} · ${fechaCorta(contrato.fecha_inicio)} a ${fechaCorta(contrato.fecha_fin)}`,
        cuerpo: `
          <div class="detalle-grid">
            <div class="detalle-campo"><small>Cliente</small><strong>${escapar(contrato.cliente_nombre)}</strong></div>
            <div class="detalle-campo"><small>Documento</small><strong>${escapar(contrato.cliente_documento || "—")}</strong></div>
            <div class="detalle-campo"><small>Valor total</small><strong>${moneda(contrato.valor_total)}</strong></div>
            <div class="detalle-campo"><small>Servicios</small><strong>${servicios.length}</strong></div>
          </div>
          <p class="seccion-titulo">Servicios contratados (documento embebido)</p>
          <div class="tabla-wrap"><table class="tabla" style="min-width:480px">
            <thead><tr><th>Servicio</th><th>Descripción</th><th class="num">Precio acordado</th></tr></thead>
            <tbody>${servicios.map((s) => `<tr><td class="principal">${escapar(s.nombre)}</td><td class="secundario">${escapar(s.descripcion)}</td><td class="num">${moneda(s.precio_acordado)}</td></tr>`).join("")}</tbody>
          </table></div>`,
        pie: `<button class="btn btn-ghost" type="button" id="btn-cancelar">Cerrar</button>`,
      });
      document.getElementById("btn-cancelar").addEventListener("click", V.cerrarModal);
    }

    contenedor.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "ver") verDetalle(registro);
      if (boton.dataset.accion === "editar") V.formularios.contratos(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/servicios_contratos/${registro._id}`, "este contrato", cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.contratos(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-estado").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     PERSONAL
     ============================================================ */
  async function personal(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar por nombre, documento, correo o especialidad…")}
        ${selectFiltro("filtro-cargo", "Todos los cargos", ["Jardinero", "Paisajista", "Especialista botánico", "Supervisor", "Auxiliar de jardinería"])}
        ${selectFiltro("filtro-estado", "Todos los estados", ["Activo", "Inactivo"])}
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nuevo trabajador</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const cargo = document.getElementById("filtro-cargo").value;
      const estado = document.getElementById("filtro-estado").value;
      if (q) params.set("q", q);
      if (cargo) params.set("cargo", cargo);
      if (estado) params.set("estado", estado);
      try {
        const r = await V.api.get("/personal?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> trabajadores`;
        contenedor.innerHTML = tabla(
          ["Trabajador", "Documento", "Cargo", "Especialidades", "Salario", "Estado", ""],
          datos.map((p) => `
            <tr>
              <td><div class="principal">${escapar(p.nombre)}</div><div class="secundario">${escapar(p.correo)} · ${escapar(p.telefono)}</div></td>
              <td>${escapar(p.documento)}</td>
              <td>${chip(p.cargo, "neutro")}</td>
              <td><div class="chips">${(p.especialidades || []).slice(0, 3).map((e) => chip(e)).join("") || '<span class="secundario">—</span>'}</div></td>
              <td class="num">${p.salario ? moneda(p.salario) : "—"}</td>
              <td>${badge(p.estado)}</td>
              <td>${acciones(p._id)}</td>
            </tr>`),
          V.vacio("👷", "No hay trabajadores", "Registre personal técnico u operativo.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar personal", error.message);
      }
    }

    contenedor.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "editar") V.formularios.personal(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/personal/${registro._id}`, `al trabajador "${registro.nombre}"`, cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.personal(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-cargo").addEventListener("change", cargar);
    document.getElementById("filtro-estado").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     VISITAS
     ============================================================ */
  async function visitas(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar en actividades u observaciones…")}
        ${selectFiltro("filtro-estado", "Todos los estados", ["Programada", "En proceso", "Finalizada", "Cancelada"])}
        <input type="date" id="filtro-desde" title="Desde" />
        <input type="date" id="filtro-hasta" title="Hasta" />
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nueva visita</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const estado = document.getElementById("filtro-estado").value;
      const desde = document.getElementById("filtro-desde").value;
      const hasta = document.getElementById("filtro-hasta").value;
      if (q) params.set("q", q);
      if (estado) params.set("estado", estado);
      if (desde) params.set("desde", desde);
      if (hasta) params.set("hasta", hasta + "T23:59:59");
      try {
        const r = await V.api.get("/visitas_mantenimiento?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> visitas`;
        contenedor.innerHTML = tabla(
          ["Fecha programada", "Propiedad / Cliente", "Contrato", "Personal", "Insumos", "Estado", ""],
          datos.map((v) => `
            <tr>
              <td><div class="principal">${fecha(v.fecha_programada, true)}</div><div class="secundario">${escapar(v.propiedad_ciudad)}</div></td>
              <td><div class="principal">${escapar(v.propiedad_nombre)}</div><div class="secundario">${escapar(v.cliente_nombre)}</div></td>
              <td>${badge(v.contrato_estado)}<div class="secundario" style="margin-top:3px">${(v.servicios_contratados || []).slice(0, 2).map(escapar).join(" · ") || "—"}</div></td>
              <td><span class="chip azul">${numero(v.total_personal)}</span></td>
              <td><span class="chip ${v.total_insumos ? "" : "neutro"}">${numero(v.total_insumos)}</span></td>
              <td>${badge(v.estado)}</td>
              <td>${acciones(v._id, { ver: true })}</td>
            </tr>`),
          V.vacio("🗓️", "No hay visitas", "Programe una visita o ajuste los filtros.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar visitas", error.message);
      }
    }

    function verDetalle(visita) {
      V.abrirModal({
        titulo: "Visita de mantenimiento",
        subtitulo: `${fecha(visita.fecha_programada, true)} · ${visita.estado}`,
        ancho: "modal-lg",
        cuerpo: `
          <div class="detalle-grid">
            <div class="detalle-campo"><small>Propiedad</small><strong>${escapar(visita.propiedad_nombre)}</strong></div>
            <div class="detalle-campo"><small>Cliente</small><strong>${escapar(visita.cliente_nombre)}</strong></div>
            <div class="detalle-campo"><small>Contrato</small><strong>${escapar(visita.contrato_estado)}</strong></div>
            <div class="detalle-campo"><small>Ciudad</small><strong>${escapar(visita.propiedad_ciudad)}</strong></div>
          </div>
          <p class="seccion-titulo">Personal asignado</p>
          <div class="chips">${(visita.personal_asignado || []).map((p) => chip(p.nombre)).join("") || '<span class="secundario">Sin personal asignado.</span>'}</div>
          <p class="seccion-titulo">Servicios del contrato</p>
          <div class="chips">${(visita.servicios_contratados || []).map((s) => chip(s, "neutro")).join("") || '<span class="secundario">Sin servicios.</span>'}</div>
          <p class="seccion-titulo">Insumos utilizados</p>
          ${(visita.insumos_utilizados || []).length ? `<div class="tabla-wrap"><table class="tabla" style="min-width:420px">
            <thead><tr><th>Insumo</th><th class="num">Cantidad</th><th>Unidad</th></tr></thead>
            <tbody>${visita.insumos_utilizados.map((i) => `<tr><td>${escapar(i.nombre)}</td><td class="num">${numero(i.cantidad)}</td><td>${escapar(i.unidad_medida)}</td></tr>`).join("")}</tbody>
          </table></div>` : '<p class="secundario">Sin consumo de insumos.</p>'}
          <p class="seccion-titulo">Actividades realizadas</p>
          ${(visita.actividades_realizadas || []).length ? `<ul class="detalle-lista">${visita.actividades_realizadas.map((a) => `<li>${escapar(a)}</li>`).join("")}</ul>` : '<p class="secundario">Sin actividades registradas.</p>'}
          <p class="seccion-titulo">Observaciones</p>
          ${(visita.observaciones || []).length ? `<ul class="detalle-lista">${visita.observaciones.map((o) => `<li>${escapar(o)}</li>`).join("")}</ul>` : '<p class="secundario">Sin observaciones.</p>'}`,
        pie: `<button class="btn btn-ghost" type="button" id="btn-cancelar">Cerrar</button>`,
      });
      document.getElementById("btn-cancelar").addEventListener("click", V.cerrarModal);
    }

    contenedor.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "ver") verDetalle(registro);
      if (boton.dataset.accion === "editar") V.formularios.visitas(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/visitas_mantenimiento/${registro._id}`, "esta visita de mantenimiento", cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.visitas(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-estado").addEventListener("change", cargar);
    document.getElementById("filtro-desde").addEventListener("change", cargar);
    document.getElementById("filtro-hasta").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     INSUMOS
     ============================================================ */
  async function insumos(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar insumo por nombre o descripción…")}
        ${selectFiltro("filtro-estado", "Todos los estados", ["Disponible", "Bajo stock", "Agotado"])}
        <label class="filtro-check"><input type="checkbox" id="filtro-bajo" /> Solo stock crítico</label>
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nuevo insumo</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const estado = document.getElementById("filtro-estado").value;
      if (q) params.set("q", q);
      if (estado) params.set("estado", estado);
      if (document.getElementById("filtro-bajo").checked) params.set("bajo_stock", "true");
      try {
        const r = await V.api.get("/insumos?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> insumos`;
        contenedor.innerHTML = tabla(
          ["Insumo", "Unidad", "Existencias", "Stock mínimo", "Estado", ""],
          datos.map((i) => `
            <tr>
              <td><div class="principal">${escapar(i.nombre)}</div><div class="secundario">${escapar(i.descripcion || "Sin descripción")}</div></td>
              <td>${escapar(i.unidad_medida)}</td>
              <td class="num principal">${numero(i.existencias)}</td>
              <td class="num">${numero(i.stock_minimo)}</td>
              <td>${badge(i.estado)}</td>
              <td>${acciones(i._id)}</td>
            </tr>`),
          V.vacio("🌱", "No hay insumos", "Registre insumos para controlar el inventario.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar insumos", error.message);
      }
    }

    contenedor.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "editar") V.formularios.insumos(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/insumos/${registro._id}`, `el insumo "${registro.nombre}"`, cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.insumos(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-estado").addEventListener("change", cargar);
    document.getElementById("filtro-bajo").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     ANALÍTICA · CINCO CONSULTAS DE AGREGACIÓN
     ============================================================ */
  function tarjetaReporte(numeroReporte, titulo, descripcion, etapas, cuerpo) {
    return `<section class="card reporte">
      <header class="reporte-head">
        <div class="titulo">
          <span class="reporte-num">${numeroReporte}</span>
          <div><h3>${escapar(titulo)}</h3><p>${escapar(descripcion)}</p></div>
        </div>
        <div class="pipeline-tags">${etapas.map((e) => `<code>${escapar(e)}</code>`).join("")}</div>
      </header>
      ${cuerpo}
    </section>`;
  }

  async function analitica(cont) {
    V.cargando(cont);
    let clientesProp, visitasDetalle, visitasEstado, insumosTop, serviciosTop;
    try {
      [clientesProp, visitasDetalle, visitasEstado, insumosTop, serviciosTop] = await Promise.all([
        V.api.get("/analitica/clientes-propiedades"),
        V.api.get("/analitica/visitas-detalle"),
        V.api.get("/analitica/visitas-estado"),
        V.api.get("/analitica/insumos-mas-utilizados?limite=8"),
        V.api.get("/analitica/servicios-mas-contratados"),
      ]);
    } catch (error) {
      cont.innerHTML = `<div class="card">${V.vacio("⚠️", "No fue posible cargar la analítica", error.message)}</div>`;
      return;
    }

    const a = clientesProp.datos || [];
    const b = visitasDetalle.datos || [];
    const c = visitasEstado.datos || [];
    const d = insumosTop.datos || [];
    const e = serviciosTop.datos || [];

    cont.innerHTML = `<div class="analitica-grid">
      ${tarjetaReporte(1, "Clientes y sus propiedades", "Total de propiedades, área gestionada y especies por cliente", ["$lookup", "$addFields", "$project", "$sort"], `
        <div class="reporte-cuerpo con-grafico">
          <div class="reporte-tabla">
            ${tabla(["Cliente", "Propiedades", "Área total", "Especies", "Detalle"], a.map((x) => `
              <tr>
                <td><div class="principal">${escapar(x.nombre)}</div><div class="secundario">${escapar(x.documento)} · ${escapar(x.estado)}</div></td>
                <td class="num principal">${numero(x.total_propiedades)}</td>
                <td class="num">${numero(x.area_total_m2)} m²</td>
                <td class="num">${numero(x.total_especies)}</td>
                <td><div class="chips">${(x.detalle_propiedades || []).slice(0, 3).map((p) => chip(p.nombre, "neutro")).join("") || "—"}</div></td>
              </tr>`), "")}
          </div>
          <div class="reporte-grafico"><canvas id="g-clientes"></canvas></div>
        </div>`)}

      ${tarjetaReporte(2, "Visitas con detalle completo", "Propiedad, cliente, contrato, personal e insumos de cada visita", ["$lookup ×3", "$unwind", "$project", "$sort"], `
        <div class="reporte-tabla" style="max-height:460px">
          ${tabla(["Fecha", "Propiedad", "Cliente", "Contrato", "Personal", "Insumos", "Estado"], b.map((x) => `
            <tr>
              <td>${fecha(x.fecha_programada, true)}</td>
              <td><div class="principal">${escapar(x.propiedad_nombre)}</div><div class="secundario">${escapar(x.propiedad_ciudad)}</div></td>
              <td>${escapar(x.cliente_nombre)}</td>
              <td>${badge(x.contrato_estado)}</td>
              <td><div class="chips">${(x.personal_asignado || []).map((p) => chip(p)).join("") || "—"}</div></td>
              <td><div class="chips">${(x.insumos_utilizados || []).map((i) => chip(`${i.nombre} ×${i.cantidad}`, "neutro")).join("") || "—"}</div></td>
              <td>${badge(x.estado)}</td>
            </tr>`), "")}
        </div>`)}

      ${tarjetaReporte(3, "Distribución de visitas por estado", "Conteo y porcentaje de participación de cada estado", ["$facet", "$group", "$unwind", "$project", "$sort"], `
        <div class="reporte-cuerpo con-grafico">
          <div class="reporte-tabla">
            ${tabla(["Estado", "Total", "Porcentaje"], c.map((x) => `
              <tr><td>${badge(x.estado)}</td><td class="num principal">${numero(x.total)}</td>
              <td class="num">${numero(x.porcentaje, 1)}%</td></tr>`), "")}
          </div>
          <div class="reporte-grafico"><canvas id="g-estados"></canvas></div>
        </div>`)}

      ${tarjetaReporte(4, "Insumos más utilizados", "Ranking por cantidad consumida y estado actual del inventario", ["$unwind", "$group", "$lookup", "$sort", "$limit"], `
        <div class="reporte-cuerpo con-grafico">
          <div class="reporte-tabla">
            ${tabla(["Insumo", "Cantidad total", "Visitas", "Existencias", "Estado"], d.map((x) => `
              <tr><td class="principal">${escapar(x.nombre)}</td>
              <td class="num">${numero(x.cantidad_total)} ${escapar(x.unidad_medida)}</td>
              <td class="num">${numero(x.total_visitas)}</td>
              <td class="num">${numero(x.existencias_actuales)}</td>
              <td>${badge(x.estado_inventario)}</td></tr>`), "")}
          </div>
          <div class="reporte-grafico"><canvas id="g-insumos"></canvas></div>
        </div>`)}

      ${tarjetaReporte(5, "Servicios más contratados", "Frecuencia, ingreso total y precio promedio por servicio", ["$unwind", "$group", "$project", "$sort"], `
        <div class="reporte-cuerpo con-grafico">
          <div class="reporte-tabla">
            ${tabla(["Servicio", "Veces contratado", "Ingreso total", "Precio promedio"], e.map((x) => `
              <tr><td class="principal">${escapar(x.servicio)}</td>
              <td class="num">${numero(x.veces_contratado)}</td>
              <td class="num">${moneda(x.ingreso_total)}</td>
              <td class="num">${moneda(x.precio_promedio)}</td></tr>`), "")}
          </div>
          <div class="reporte-grafico"><canvas id="g-servicios"></canvas></div>
        </div>`)}
    </div>`;

    if (!window.Chart) return;

    const verde = "#2b8150", lima = "#b7d94b", ambar = "#c07a13", azul = "#2a6f97";
    const baseOpciones = {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10, family: "Manrope" }, color: "#5b6b60" } },
        y: { beginAtZero: true, grid: { color: "#f0eee4" }, ticks: { font: { size: 10, family: "Manrope" }, color: "#5b6b60" } },
      },
    };

    if (document.getElementById("g-clientes")) {
      registrarGrafico(new Chart(document.getElementById("g-clientes"), {
        type: "bar",
        data: {
          labels: a.slice(0, 8).map((x) => x.nombre.length > 18 ? x.nombre.slice(0, 17) + "…" : x.nombre),
          datasets: [{ label: "Área total (m²)", data: a.slice(0, 8).map((x) => x.area_total_m2), backgroundColor: verde, borderRadius: 6 }],
        },
        options: baseOpciones,
      }));
    }

    if (document.getElementById("g-estados")) {
      registrarGrafico(new Chart(document.getElementById("g-estados"), {
        type: "doughnut",
        data: {
          labels: c.map((x) => x.estado),
          datasets: [{ data: c.map((x) => x.total), backgroundColor: [verde, ambar, lima, "#9aa79d"], borderWidth: 2, borderColor: "#fff" }],
        },
        options: {
          responsive: true, maintainAspectRatio: false, cutout: "60%",
          plugins: { legend: { position: "bottom", labels: { boxWidth: 9, usePointStyle: true, font: { size: 11, family: "Manrope" } } } },
        },
      }));
    }

    if (document.getElementById("g-insumos")) {
      registrarGrafico(new Chart(document.getElementById("g-insumos"), {
        type: "bar",
        data: {
          labels: d.map((x) => x.nombre.length > 16 ? x.nombre.slice(0, 15) + "…" : x.nombre),
          datasets: [{ label: "Cantidad consumida", data: d.map((x) => x.cantidad_total), backgroundColor: lima, borderRadius: 6 }],
        },
        options: { ...baseOpciones, indexAxis: "y", scales: { x: { beginAtZero: true, grid: { color: "#f0eee4" } }, y: { grid: { display: false } } } },
      }));
    }

    const opcionesHorizontales = {
      ...baseOpciones,
      indexAxis: "y",
      scales: { x: { beginAtZero: true, grid: { color: "#f0eee4" } }, y: { grid: { display: false } } },
    };

    if (document.getElementById("g-servicios")) {
      registrarGrafico(new Chart(document.getElementById("g-servicios"), {
        type: "bar",
        data: {
          labels: e.slice(0, 8).map((x) => x.servicio.length > 16 ? x.servicio.slice(0, 15) + "…" : x.servicio),
          datasets: [{ label: "Veces contratado", data: e.slice(0, 8).map((x) => x.veces_contratado), backgroundColor: azul, borderRadius: 6 }],
        },
        options: opcionesHorizontales,
      }));
    }
  }

  window.Verde.vistas = {
    panel, clientes, propiedades, contratos, personal, visitas, insumos, analitica, destruirGraficos,
  };
})();
