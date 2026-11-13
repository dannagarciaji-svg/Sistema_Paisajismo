/* ============================================================
   VerdeVivo · Enrutador y arranque de la aplicación
   ============================================================ */
(function () {
  "use strict";
  const V = window.Verde;
  const contenido = document.getElementById("contenido");
  const titulo = document.getElementById("titulo-vista");
  const subtitulo = document.getElementById("subtitulo-vista");
  const sidebar = document.getElementById("sidebar");

  const RUTAS = {
    panel: {
      titulo: "Panel general",
      subtitulo: "Resumen operativo del sistema de paisajismo",
      render: V.vistas.panel,
    },
    clientes: {
      titulo: "Clientes",
      subtitulo: "Personas y empresas que contratan los servicios",
      render: V.vistas.clientes,
    },
    propiedades: {
      titulo: "Propiedades y control botánico",
      subtitulo: "Predios gestionados y especies vegetales registradas",
      render: V.vistas.propiedades,
    },
    contratos: {
      titulo: "Servicios y contratos",
      subtitulo: "Servicios contratados, vigencias y valor acordado",
      render: V.vistas.contratos,
    },
    personal: {
      titulo: "Personal técnico y operativo",
      subtitulo: "Jardineros, paisajistas y especialistas botánicos",
      render: V.vistas.personal,
    },
    visitas: {
      titulo: "Visitas de mantenimiento",
      subtitulo: "Programación, ejecución y consumo de insumos",
      render: V.vistas.visitas,
    },
    insumos: {
      titulo: "Insumos e inventario",
      subtitulo: "Existencias, stock mínimo y alertas de reposición",
      render: V.vistas.insumos,
    },
    analitica: {
      titulo: "Analítica y reportes",
      subtitulo: "Cinco consultas de agregación sobre MongoDB Atlas",
      render: V.vistas.analitica,
    },
  };

  let vistaActual = "panel";
  let renderizando = false;

  function rutaActual() {
    const hash = (location.hash || "#/panel").replace(/^#\/?/, "").split("?")[0];
    return RUTAS[hash] ? hash : "panel";
  }

  async function renderizar() {
    if (renderizando) return;
    renderizando = true;
    const clave = rutaActual();
    vistaActual = clave;
    const config = RUTAS[clave];

    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("activo", item.dataset.vista === clave);
    });
    titulo.textContent = config.titulo;
    subtitulo.textContent = config.subtitulo;
    document.title = `${config.titulo} · VerdeVivo`;

    V.vistas.destruirGraficos();
    sidebar.classList.remove("abierto");

    try {
      await config.render(contenido);
    } catch (error) {
      contenido.innerHTML = `<div class="card">${V.vacio("⚠️", "Ocurrió un error al cargar la vista", error.message)}</div>`;
    } finally {
      renderizando = false;
    }
  }

  async function verificarConexion() {
    const caja = document.getElementById("db-status");
    try {
      const r = await V.api.get("/api/health");
      const conteos = r.colecciones || {};
      const total = Object.values(conteos).reduce((a, b) => a + b, 0);
      caja.innerHTML = `
        <span class="dot dot-ok"></span>
        <div><strong>Base de datos conectada</strong><small>${V.escapar(r.base_de_datos)} · ${total} documentos</small></div>`;
    } catch (error) {
      caja.innerHTML = `
        <span class="dot dot-error"></span>
        <div><strong>Sin conexión a la base</strong><small>${V.escapar(error.message.slice(0, 46))}</small></div>`;
    }
  }

  document.getElementById("btn-refrescar").addEventListener("click", () => {
    renderizar();
    verificarConexion();
    V.toast("Datos actualizados.", "info", "Actualización");
  });

  document.getElementById("btn-menu").addEventListener("click", () => {
    sidebar.classList.toggle("abierto");
  });

  window.addEventListener("hashchange", renderizar);

  document.addEventListener("click", (e) => {
    if (window.innerWidth <= 860 && sidebar.classList.contains("abierto") &&
        !sidebar.contains(e.target) && !e.target.closest("#btn-menu")) {
      sidebar.classList.remove("abierto");
    }
  });

  function iniciar() {
    if (!location.hash) location.hash = "#/panel";
    verificarConexion();
    renderizar();
    setInterval(verificarConexion, 60000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
