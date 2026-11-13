/* ============================================================
   VerdeVivo · Utilidades de cliente: API, formato, interfaz
   ============================================================ */
(function () {
  "use strict";

  const API = "";

  /* ------------------------- HTTP ------------------------- */
  async function peticion(ruta, opciones = {}) {
    const config = {
      method: opciones.method || "GET",
      headers: { "Content-Type": "application/json" },
    };
    if (opciones.body !== undefined) config.body = JSON.stringify(opciones.body);

    let respuesta;
    try {
      respuesta = await fetch(API + ruta, config);
    } catch (error) {
      throw new Error("No fue posible comunicarse con el servidor. Verifique su conexión.");
    }

    let cuerpo = null;
    const texto = await respuesta.text();
    if (texto) {
      try { cuerpo = JSON.parse(texto); } catch (_) { cuerpo = { error: texto }; }
    }

    if (!respuesta.ok) {
      const detalle = cuerpo && cuerpo.detalles && cuerpo.detalles.length
        ? " " + cuerpo.detalles.join(" · ")
        : "";
      const error = new Error(((cuerpo && cuerpo.error) || "Error inesperado del servidor.") + detalle);
      error.estado = respuesta.status;
      error.cuerpo = cuerpo;
      throw error;
    }
    return cuerpo;
  }

  const api = {
    get: (ruta) => peticion(ruta),
    post: (ruta, body) => peticion(ruta, { method: "POST", body }),
    put: (ruta, body) => peticion(ruta, { method: "PUT", body }),
    del: (ruta) => peticion(ruta, { method: "DELETE" }),
  };

  /* ------------------------- Formato ------------------------- */
  const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

  function escapar(valor) {
    return String(valor === null || valor === undefined ? "" : valor)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function moneda(valor) {
    const numero = Number(valor || 0);
    return "$" + numero.toLocaleString("es-CO", { maximumFractionDigits: 0 });
  }

  function numero(valor, decimales = 0) {
    return Number(valor || 0).toLocaleString("es-CO", {
      minimumFractionDigits: decimales,
      maximumFractionDigits: decimales,
    });
  }

  function fecha(valor, conHora = false) {
    if (!valor) return "—";
    const d = new Date(valor);
    if (Number.isNaN(d.getTime())) return String(valor);
    const base = `${String(d.getUTCDate()).padStart(2, "0")} ${MESES[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
    if (!conHora) return base;
    const h = String(d.getUTCHours()).padStart(2, "0");
    const m = String(d.getUTCMinutes()).padStart(2, "0");
    return `${base} · ${h}:${m}`;
  }

  function fechaCorta(valor) {
    if (!valor) return "—";
    const d = new Date(valor);
    if (Number.isNaN(d.getTime())) return String(valor);
    return `${String(d.getUTCDate()).padStart(2, "0")}/${String(d.getUTCMonth() + 1).padStart(2, "0")}/${d.getUTCFullYear()}`;
  }

  function paraInputFecha(valor, conHora = true) {
    if (!valor) return "";
    const d = new Date(valor);
    if (Number.isNaN(d.getTime())) return String(valor).slice(0, conHora ? 16 : 10);
    const iso = d.toISOString();
    return conHora ? iso.slice(0, 16) : iso.slice(0, 10);
  }

  function iniciales(nombre) {
    return String(nombre || "?")
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0].toUpperCase())
      .join("");
  }

  /* ------------------------- Badges ------------------------- */
  const CLASES_ESTADO = {
    Activo: "verde", Inactivo: "gris",
    Disponible: "verde", "Bajo stock": "ambar", Agotado: "rojo",
    Programada: "azul", "En proceso": "ambar", Finalizada: "verde", Cancelada: "gris",
    Suspendido: "ambar", Vencido: "rojo",
  };

  function badge(estado) {
    const clase = CLASES_ESTADO[estado] || "gris";
    return `<span class="badge badge-${clase}">${escapar(estado || "—")}</span>`;
  }

  function chip(texto, clase = "") {
    return `<span class="chip ${clase}">${escapar(texto)}</span>`;
  }

  /* ------------------------- Toasts ------------------------- */
  function toast(mensaje, tipo = "ok", titulo) {
    const contenedor = document.getElementById("toasts");
    if (!contenedor) return;
    const el = document.createElement("div");
    el.className = "toast " + (tipo === "error" ? "error" : tipo === "info" ? "info" : "");
    const titulos = { ok: "Operación exitosa", error: "No se pudo completar", info: "Información" };
    el.innerHTML = `
      <div>
        <strong>${escapar(titulo || titulos[tipo] || titulos.ok)}</strong>
        <small>${escapar(mensaje)}</small>
      </div>`;
    contenedor.appendChild(el);
    setTimeout(() => {
      el.style.transition = "opacity .25s, transform .25s";
      el.style.opacity = "0";
      el.style.transform = "translateX(16px)";
      setTimeout(() => el.remove(), 260);
    }, tipo === "error" ? 6200 : 3800);
  }

  /* ------------------------- Modal ------------------------- */
  const modal = document.getElementById("modal");
  const modalTitulo = document.getElementById("modal-titulo");
  const modalSub = document.getElementById("modal-subtitulo");
  const modalCuerpo = document.getElementById("modal-cuerpo");
  const modalPie = document.getElementById("modal-pie");

  function abrirModal({ titulo, subtitulo = "", cuerpo, pie = "", ancho = "" }) {
    modalTitulo.textContent = titulo;
    modalSub.textContent = subtitulo;
    modalCuerpo.innerHTML = cuerpo;
    modalPie.innerHTML = pie;
    modal.querySelector(".modal").className = "modal " + ancho;
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    const primero = modalCuerpo.querySelector("input, select, textarea, button");
    if (primero) setTimeout(() => primero.focus(), 60);
  }

  function cerrarModal() {
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  /* ------------------------- Confirmación ------------------------- */
  const confirmacion = document.getElementById("confirmacion");
  let resolverConfirmacion = null;

  function confirmar({ titulo = "Confirmar acción", texto = "¿Desea continuar?", etiqueta = "Sí, continuar" }) {
    document.getElementById("confirmar-titulo").textContent = titulo;
    document.getElementById("confirmar-texto").textContent = texto;
    document.getElementById("confirmar-si").textContent = etiqueta;
    confirmacion.hidden = false;
    document.body.style.overflow = "hidden";
    return new Promise((resolver) => { resolverConfirmacion = resolver; });
  }

  function finalizarConfirmacion(valor) {
    confirmacion.hidden = true;
    document.body.style.overflow = "";
    if (resolverConfirmacion) resolverConfirmacion(valor);
    resolverConfirmacion = null;
  }

  /* ------------------------- Varios ------------------------- */
  function cargando(contenedor) {
    contenedor.innerHTML = `
      <div class="skeleton-wrap">
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>
      </div>`;
  }

  function vacio(emoji, titulo, detalle) {
    return `<div class="vacio"><span class="emoji">${emoji}</span><strong>${escapar(titulo)}</strong><small>${escapar(detalle)}</small></div>`;
  }

  function boton(codigo) {
    return `<button class="btn btn-primario" id="btn-guardar" type="submit">${codigo}</button>`;
  }

  const iconos = {
    editar: '<svg viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>',
    eliminar: '<svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>',
    ver: '<svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17a5 5 0 1 1 0-10 5 5 0 0 1 0 10zm0-8a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/></svg>',
    mas: '<svg viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>',
    buscar: '<svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 1 0-.7.7l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/></svg>',
  };

  window.Verde = {
    api, peticion,
    escapar, moneda, numero, fecha, fechaCorta, paraInputFecha, iniciales,
    badge, chip, toast, abrirModal, cerrarModal, confirmar, finalizarConfirmacion,
    cargando, vacio, boton, iconos,
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("modal-cerrar").addEventListener("click", cerrarModal);
    modal.addEventListener("click", (e) => { if (e.target === modal) cerrarModal(); });
    document.getElementById("confirmar-no").addEventListener("click", () => finalizarConfirmacion(false));
    document.getElementById("confirmar-si").addEventListener("click", () => finalizarConfirmacion(true));
    confirmacion.addEventListener("click", (e) => { if (e.target === confirmacion) finalizarConfirmacion(false); });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        if (!confirmacion.hidden) finalizarConfirmacion(false);
        else if (!modal.hidden) cerrarModal();
      }
    });
  });
})();
