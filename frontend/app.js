document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("formLogin");
    if (form) form.addEventListener("submit", validarLogin);

    const checkbox = document.getElementById("btn-modal");
    if (checkbox) checkbox.checked = false;

    if (document.getElementById("inicio")) {
        iniciarPerfil();
        cargarActividades();
        verificarActividadEnCurso();
    }
});

// ==================== LOGIN ====================
function mostrarModal(mensaje, titulo = "Aviso") {
    document.getElementById("modalTitulo").innerText = titulo;
    document.getElementById("modalMensaje").innerText = mensaje;
    document.getElementById("btn-modal").checked = true;
}

function validarEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

async function validarLogin(event) {
    event.preventDefault();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    if (!validarEmail(email)) {
        mostrarModal("Correo electrónico inválido", "Error");
        return;
    }
    if (password.length < 6) {
        mostrarModal("La contraseña debe tener mínimo 6 caracteres", "Error");
        return;
    }

    const boton = event.target.querySelector("button");
    const textoOriginal = boton.textContent;
    boton.textContent = "Ingresando...";
    boton.disabled = true;

    try {
        const respuesta = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const resultado = await respuesta.json();

        if (respuesta.ok) {
            localStorage.setItem("usuario_id", resultado.usuario_id);
            localStorage.setItem("usuario_nombre", resultado.nombre);

            try {
                await fetch(`/api/mfa/enviar/${resultado.usuario_id}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ tipo: "login" })
                });
                mostrarModal("Código enviado a tu correo", "Verificación");
                setTimeout(() => {
                    window.location.href = `verificar.html?id=${resultado.usuario_id}&tipo=login`;
                }, 1500);
            } catch (e) {
                mostrarModal("Error enviando código MFA", "Error");
            }

        } else if (respuesta.status === 403) {
            // Cuenta no verificada — obtener id del header
            const usuarioIdTemp = respuesta.headers.get("X-Usuario-Id");
            if (usuarioIdTemp) {
                localStorage.setItem("usuario_id_temp", usuarioIdTemp);
            }
            mostrarModalVerificacion(resultado.detail);

        } else {
            mostrarModal(resultado.detail || "Error al iniciar sesión", "Error");
        }

    } catch (error) {
        console.error(error);
        mostrarModal("Error de conexión con el servidor", "Error");
    } finally {
        boton.textContent = textoOriginal;
        boton.disabled = false;
    }
}

function mostrarModalVerificacion(mensaje) {
    document.getElementById("modalTitulo").innerText = "Cuenta no verificada";
    document.getElementById("modalMensaje").innerText = mensaje;

    const btnCerrar = document.querySelector(".btn-cerrar");
    btnCerrar.innerHTML = `
        <label for="btn-modal" onclick="irAVerificar()" 
               style="padding:8px 14px; background:#4CB8A4; color:white; border-radius:6px; cursor:pointer;">
            Verificar ahora
        </label>
        <label for="btn-modal" 
               style="padding:8px 14px; background:#334155; color:white; border-radius:6px; cursor:pointer; margin-left:8px;">
            Cerrar
        </label>
    `;
    document.getElementById("btn-modal").checked = true;
}

function irAVerificar() {
    const usuarioId = localStorage.getItem("usuario_id_temp");
    if (!usuarioId) {
        mostrarModal("No se pudo obtener el usuario. Regístrate de nuevo.", "Error");
        return;
    }
    window.location.href = `verificar.html?id=${usuarioId}&tipo=registro`;
}
function mostrarModalVerificacion(mensaje) {
    document.getElementById("modalTitulo").innerText = "Cuenta no verificada";
    document.getElementById("modalMensaje").innerText = mensaje;

    const btnCerrar = document.querySelector(".btn-cerrar");
    btnCerrar.innerHTML = `
        <label for="btn-modal" onclick="irAVerificar()" 
               style="padding:8px 14px; background:#4CB8A4; color:white; border-radius:6px; cursor:pointer;">
            Verificar ahora
        </label>
        <label for="btn-modal" 
               style="padding:8px 14px; background:#334155; color:white; border-radius:6px; cursor:pointer; margin-left:8px;">
            Cerrar
        </label>
    `;
    document.getElementById("btn-modal").checked = true;
}

function irAVerificar() {
    const usuarioId = localStorage.getItem("usuario_id_temp");
    if (!usuarioId) {
        mostrarModal("No se pudo obtener el usuario. Regístrate de nuevo.", "Error");
        return;
    }
    window.location.href = `verificar.html?id=${usuarioId}&tipo=registro`;
}












// ==================== SESIÓN Y PERFIL ====================
async function iniciarPerfil() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) {
        window.location.href = "login.html";
        return;
    }

    try {
        const [resPerfil, resActividades] = await Promise.all([
            fetch(`/api/perfil/${usuarioId}`),
            fetch(`/api/actividades/${usuarioId}`)
        ]);

        const perfil = await resPerfil.json();
        const actividades = await resActividades.json();

        pintarPerfil(perfil);
        cargarInicio(perfil, actividades);
        verificarEncuestaHoy();

    } catch (error) {
        console.error("Error cargando datos:", error);
    }
}

function pintarPerfil(datos) {
    document.getElementById("perfil-nombre").value         = datos.nombre        || "";
    document.getElementById("perfil-email").value          = datos.email         || "";
    document.getElementById("perfil-edad").value           = datos.edad          || "";
    document.getElementById("perfil-horas-trabajo").value  = datos.horas_trabajo  || 0;
    document.getElementById("perfil-horas-descanso").value = datos.horas_descanso || 0;

    const selectTipo = document.getElementById("perfil-tipo");
    if (selectTipo) selectTipo.value = datos.tipo_usuario || "Estudiante";

    const selectNivel = document.getElementById("perfil-nivel");
    if (selectNivel) selectNivel.value = datos.nivel_carga || "Medio";

    const h2 = document.querySelector(".perfil-top h2");
    if (h2) h2.textContent = datos.nombre;
}

function mostrarSeccion(id) {
    document.querySelectorAll(".seccion").forEach(s => s.classList.remove("activa"));
    document.getElementById(id).classList.add("activa");

    // Resaltar botón activo en sidebar
    document.querySelectorAll(".menu button").forEach(b => b.classList.remove("activo"));
    const btn = document.getElementById(`btn-${id}`);
    if (btn) btn.classList.add("activo");
    
    if (id === "historial") {
        cargarHistorial();
    }
    
    if (id === "analisis") cargarAnalisis();
}



// Nueva función para cargar la fase de estrés en su pestaña
async function cargarFaseEstres() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) return;

    const faseBadge          = document.getElementById("fase-badge");
    const faseTexto          = document.getElementById("fase-texto");
    const listaRecomendaciones = document.getElementById("lista-recomendaciones");
    const barraProgreso      = document.querySelector("#fase .barra .nivel");

    faseBadge.textContent = "Calculando...";

    try {
        const res = await fetch(`/api/estres/${usuarioId}`);
        const datos = await res.json();

        faseBadge.textContent = datos.fase;
        faseBadge.className = `fase-indicador fase-${datos.fase.toLowerCase()}`;

        faseTexto.textContent = `Fase actual: ${datos.fase} — Puntuación: ${datos.puntos}/12`;

        if (barraProgreso) {
            barraProgreso.style.width = datos.porcentaje + "%";
            barraProgreso.style.backgroundColor = datos.color;
        }

        listaRecomendaciones.innerHTML = datos.recomendaciones.map(rec => `
            <div class="recomendacion-item">
                <div class="rec-icono">${rec.icono}</div>
                <div class="rec-texto">${rec.texto}</div>
            </div>
        `).join("");

    } catch (error) {
        console.error(error);
        faseBadge.textContent = "Error";
        listaRecomendaciones.innerHTML = "<p style='color:#ef4444;'>No se pudo cargar el análisis.</p>";
    }
}


function cerrarSesion() {
    localStorage.removeItem("usuario_id");
    localStorage.removeItem("usuario_nombre");
    window.location.href = "login.html";
}

async function guardarPerfil() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) return;

    const datos = {
        nombre:         document.getElementById("perfil-nombre").value.trim(),
        edad:           parseInt(document.getElementById("perfil-edad").value) || null,
        tipo_usuario:   document.getElementById("perfil-tipo").value,
        nivel_carga:    document.getElementById("perfil-nivel").value,
        horas_trabajo:  parseInt(document.getElementById("perfil-horas-trabajo").value) || 0,
        horas_descanso: parseInt(document.getElementById("perfil-horas-descanso").value) || 0
    };

    try {
        const respuesta = await fetch(`/api/perfil/${usuarioId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });
        const resultado = await respuesta.json();

        if (respuesta.ok) {
            localStorage.setItem("usuario_nombre", datos.nombre);
            mostrarToast("Perfil actualizado correctamente");
            // Invalidar caché para que Gemini regenere con el nuevo perfil
            // Refrescar análisis IA después de guardar perfil
            const uid = localStorage.getItem("usuario_id");
            const [rp, ra] = await Promise.all([
                fetch(`/api/perfil/${uid}`),
                fetch(`/api/actividades/${uid}`)
            ]);
            cargarInicio(await rp.json(), await ra.json());
        } else {
            mostrarToast("Error al guardar: " + (resultado.detail || "intenta de nuevo"));
        }
    } catch (error) {
        console.error(error);
        mostrarToast("Error de conexión");
    }
}

function mostrarToast(mensaje) {
    const toast = document.getElementById("toast");
    toast.textContent = mensaje;
    toast.classList.add("visible");
    setTimeout(() => toast.classList.remove("visible"), 3000);
}

// ==================== DASHBOARD INICIO ====================
async function cargarInicio(perfil, actividades) {
    const nombre = perfil.nombre.split(" ")[0];
    document.getElementById("inicio-nombre").textContent = `Hola, ${nombre} 👋`;

    const hoy = new Date();
    const opciones = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
    document.getElementById("inicio-fecha").textContent = hoy.toLocaleDateString("es-ES", opciones);

    document.getElementById("inicio-horas-trabajo").textContent  = `${perfil.horas_trabajo}h`;
    document.getElementById("inicio-horas-descanso").textContent = `${perfil.horas_descanso}h`;

    const fechaHoy = hoy.toISOString().split("T")[0];
    const actHoy = actividades.filter(a => a.fecha === fechaHoy);
    const completadas = actHoy.filter(a => a.estado === "Completada");

    document.getElementById("inicio-actividades-hoy").textContent = actHoy.length;
    document.getElementById("inicio-completadas").textContent = completadas.length;

    const listaHoy = document.getElementById("inicio-lista-hoy");
    if (actHoy.length === 0) {
        listaHoy.innerHTML = "<p style='opacity:0.4; font-size:0.9rem;'>No tienes actividades programadas para hoy.</p>";
    } else {
        listaHoy.innerHTML = actHoy.map(a => `
            <div class="actividad-item-hoy">
                <div>
                    <div class="actividad-nombre">${escapeHtml(a.nombre)}</div>
                    <div class="actividad-meta">${a.categoria} · ${a.duracion} min</div>
                </div>
                <span class="badge badge-${a.estado === 'Completada' ? 'baja' : a.estado === 'En progreso' ? 'media' : 'alta'}">${a.estado}</span>
            </div>
        `).join("");
    }

    // Nivel de estrés
    const usuarioId = localStorage.getItem("usuario_id");
    try {
        const res = await fetch(`/api/estres/${usuarioId}`);
        const datos = await res.json();

        const badge1 = document.getElementById("inicio-badge");
        const badge2 = document.getElementById("inicio-badge-2");
        const claseColor = datos.fase === "Alarma" ? "bajo"
            : datos.fase === "Resistencia" ? "medio" : "alto";

        if (badge1) { badge1.textContent = datos.fase; badge1.className = `nivel-estres-badge estres-${claseColor}`; }
        if (badge2) { badge2.textContent = datos.fase; badge2.className = `nivel-estres-badge estres-${claseColor}`; }

        const barra = document.getElementById("barra-estres");
        if (barra) {
            barra.style.width      = datos.porcentaje + "%";
            barra.style.background = datos.color;
        }

        const detalle = document.getElementById("inicio-estres-detalle");
        if (detalle) detalle.textContent = `Puntuación: ${datos.puntos}/12 — ${getDescripcionFase(datos.fase)}`;

        const rec = document.getElementById("inicio-recomendacion");
        if (rec && datos.recomendaciones.length > 0) {
            rec.textContent = datos.recomendaciones[0].texto;
        }

    } catch (error) {
        console.error("Error estrés:", error);
        const nivelEstres = calcularEstres(perfil, actividades);
        actualizarUIEstresLocal(nivelEstres);
    }
}

// Función para actualizar la UI con datos del backend
function actualizarUIEstres(datosEstres) {
    // Actualizar badges
    const badge1 = document.getElementById("inicio-badge");
    const badge2 = document.getElementById("inicio-badge-2");
    
    if (badge1) {
        badge1.textContent = datosEstres.fase;
        badge1.className = `nivel-estres-badge estres-${datosEstres.fase === "Alarma" ? "bajo" : datosEstres.fase === "Resistencia" ? "medio" : "alto"}`;
    }
    if (badge2) {
        badge2.textContent = datosEstres.fase;
        badge2.className = `nivel-estres-badge estres-${datosEstres.fase === "Alarma" ? "bajo" : datosEstres.fase === "Resistencia" ? "medio" : "alto"}`;
    }
    
    // Actualizar barra de estrés
    const barra = document.getElementById("barra-estres");
    const colores = { 
        "Alarma": "#22c55e",      // verde
        "Resistencia": "#eab308",  // amarillo
        "Agotamiento": "#ef4444"   // rojo
    };
    const anchos = { 
        "Alarma": "25%", 
        "Resistencia": "60%", 
        "Agotamiento": "90%" 
    };
    
    if (barra) {
        barra.style.width = anchos[datosEstres.fase] || "50%";
        barra.style.background = colores[datosEstres.fase] || "#eab308";
    }
    
    // Actualizar detalle
    const detalle = document.getElementById("inicio-estres-detalle");
    if (detalle) {
        detalle.textContent = `Puntuación: ${datosEstres.puntos}/12 — ${getDescripcionFase(datosEstres.fase)}`;
    }
    
    // Actualizar recomendación
    const rec = document.getElementById("inicio-recomendacion");
    if (rec && datosEstres.recomendaciones && datosEstres.recomendaciones.length > 0) {
        rec.textContent = datosEstres.recomendaciones[0].texto;
    }
}

function actualizarUIEstresLocal(nivelEstres) {
    const badge1 = document.getElementById("inicio-badge");
    const badge2 = document.getElementById("inicio-badge-2");
    if (badge1) { 
        badge1.textContent = nivelEstres.etiqueta; 
        badge1.className = `nivel-estres-badge estres-${nivelEstres.clase}`; 
    }
    if (badge2) { 
        badge2.textContent = nivelEstres.etiqueta; 
        badge2.className = `nivel-estres-badge estres-${nivelEstres.clase}`; 
    }
    
    const barra = document.getElementById("barra-estres");
    const colores = { bajo: "#4CB8A4", medio: "#FBBF24", alto: "#EF4444" };
    const anchos  = { bajo: "30%", medio: "65%", alto: "90%" };
    if (barra) {
        barra.style.width      = anchos[nivelEstres.clase];
        barra.style.background = colores[nivelEstres.clase];
    }
    
    const detalle = document.getElementById("inicio-estres-detalle");
    const rec     = document.getElementById("inicio-recomendacion");
    if (detalle) detalle.textContent = nivelEstres.detalle;
    if (rec)     rec.textContent     = nivelEstres.recomendacion;
}

function getDescripcionFase(fase) {
    if (fase === "Alarma") return "Tu nivel de estrés es manejable. Vas por buen camino.";
    if (fase === "Resistencia") return "Nivel de estrés moderado. Toma pausas activas.";
    return "Nivel de estrés elevado. Prioriza tu bienestar.";
}

function calcularEstres(perfil, actividades) {
    let puntos = 0;

    if (perfil.nivel_carga === "Alto")  puntos += 3;
    if (perfil.nivel_carga === "Medio") puntos += 2;
    if (perfil.nivel_carga === "Bajo")  puntos += 1;

    if (perfil.horas_trabajo > 8)  puntos += 2;
    if (perfil.horas_descanso < 6) puntos += 2;
    if (perfil.horas_descanso < 4) puntos += 1;

    const hoy = new Date().toISOString().split("T")[0];
    const altasPendientes = actividades.filter(a =>
        a.fecha === hoy && a.prioridad === "Alta" && a.estado === "Pendiente"
    ).length;
    puntos += altasPendientes;

    const incumplidas = actividades.filter(a =>
        a.fecha < hoy && a.estado === "Pendiente"
    ).length;
    puntos += incumplidas * 2;

    if (puntos <= 3) return {
        etiqueta: "Estrés bajo", clase: "bajo",
        detalle: `Puntuación: ${puntos}/10 — Tu carga es manejable y tus hábitos son saludables.`,
        recomendacion: "Vas muy bien. Mantén tu ritmo actual y recuerda tomar pequeñas pausas activas durante el día."
    };
    if (puntos <= 6) return {
        etiqueta: "Estrés moderado", clase: "medio",
        detalle: `Puntuación: ${puntos}/10 — Tu carga es moderada, hay margen de mejora.`,
        recomendacion: "Tu carga es moderada. Considera redistribuir algunas actividades y asegúrate de descansar bien esta noche."
    };
    return {
        etiqueta: "Estrés alto", clase: "alto",
        detalle: `Puntuación: ${puntos}/10 — Tu nivel de carga es elevado, toma medidas hoy.`,
        recomendacion: "Tu nivel de carga es elevado. Prioriza solo las actividades urgentes y programa al menos 30 minutos de descanso activo hoy."
    };
}

function responderEncuesta(respuesta, nivel) {
    document.getElementById("encuesta-respuesta").textContent = `Registrado: ${respuesta}. ¡Gracias por compartir cómo te sientes!`;
    document.querySelectorAll(".encuesta-btn").forEach(b => b.disabled = true);
}

// ==================== ACTIVIDADES ====================
function mostrarFormActividad() {
    document.getElementById("form-actividad").style.display = "block";
    document.getElementById("act-fecha").value = new Date().toISOString().split("T")[0];
}

function ocultarFormActividad() {
    document.getElementById("form-actividad").style.display = "none";
}

async function crearActividad() {
    const usuarioId = localStorage.getItem("usuario_id");
    const nombre = document.getElementById("act-nombre").value.trim();
    const fecha  = document.getElementById("act-fecha").value;
    const duracion = parseInt(document.getElementById("act-duracion").value) || 0;
    if (duracion <= 0) { mostrarToast("La duración debe ser mayor a 0 minutos"); return; }
    if (duracion > 480) { mostrarToast("La duración no puede superar 480 minutos"); return; }

    if (!nombre) { mostrarToast("El nombre es obligatorio"); return; }
    if (!fecha)  { mostrarToast("La fecha es obligatoria");  return; }

    const datos = {
        nombre, fecha,
        duracion,
        categoria:   document.getElementById("act-categoria").value,
        prioridad:   document.getElementById("act-prioridad").value,
        descripcion: document.getElementById("act-descripcion").value.trim()
    };

    try {
        const respuesta = await fetch(`/api/actividades/${usuarioId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });
        if (respuesta.ok) {
            ocultarFormActividad();
            mostrarToast("Actividad creada");
            cargarActividades();
        } else {
            mostrarToast("Error al crear actividad");
        }
    } catch (error) {
        console.error(error);
        mostrarToast("Error de conexión");
    }
}

async function eliminarActividad(actividadId) {
    const usuarioId = localStorage.getItem("usuario_id");
    try {
        const respuesta = await fetch(`/api/actividades/${actividadId}/${usuarioId}`, { method: "DELETE" });
        if (respuesta.ok) {
            mostrarToast("Actividad eliminada");
            cargarActividades();
        }
    } catch (error) { console.error(error); }
}

async function cambiarEstado(actividadId, estado) {
    const usuarioId = localStorage.getItem("usuario_id");
    try {
        await fetch(`/api/actividades/${actividadId}/${usuarioId}/estado`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ estado })
        });
        mostrarToast("Estado actualizado");
    } catch (error) { console.error(error); }
}

// ==================== CALENDARIO ====================
let mesActual = new Date().getMonth();
let anioActual = new Date().getFullYear();
let todasActividades = [];
let diaSeleccionado = null;

function renderCalendario(actividades) {
    todasActividades = actividades;
    const meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                   "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];

    const tituloEl = document.getElementById("cal-titulo");
    if (!tituloEl) return;
    tituloEl.textContent = `${meses[mesActual]} ${anioActual}`;

    const grid = document.getElementById("calendario-grid");
    grid.innerHTML = "";

    const primerDia  = new Date(anioActual, mesActual, 1).getDay();
    const diasEnMes  = new Date(anioActual, mesActual + 1, 0).getDate();
    const fechaHoyStr = new Date().toISOString().split("T")[0];

    for (let i = 0; i < primerDia; i++) {
        const vacio = document.createElement("div");
        vacio.className = "cal-dia vacio";
        grid.appendChild(vacio);
    }

    for (let d = 1; d <= diasEnMes; d++) {
        const fecha = `${anioActual}-${String(mesActual+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
        const actsDia = actividades.filter(a => a.fecha === fecha);

        const div = document.createElement("div");
        div.className = "cal-dia";
        if (fecha === fechaHoyStr)   div.classList.add("hoy");
        if (fecha === diaSeleccionado) div.classList.add("seleccionado");

        let dotsHTML = "";
        if (actsDia.length > 0) {
            const completadas = actsDia.filter(a => a.estado === "Completada").length;
            const pendientes  = actsDia.filter(a => a.estado === "Pendiente").length;
            const enProgreso  = actsDia.filter(a => a.estado === "En progreso").length;
            dotsHTML = '<div class="cal-dots">';
            if (completadas > 0) dotsHTML += `<div class="cal-dot dot-completada"></div>`;
            if (enProgreso  > 0) dotsHTML += `<div class="cal-dot dot-parcial"></div>`;
            if (pendientes  > 0) dotsHTML += `<div class="cal-dot dot-pendiente"></div>`;
            dotsHTML += '</div>';
        }

        div.innerHTML = `<span>${d}</span>${dotsHTML}`;
        div.onclick = () => seleccionarDia(fecha, actividades);
        grid.appendChild(div);
    }
}

function seleccionarDia(fecha, actividades) {
    diaSeleccionado = fecha;
    renderCalendario(actividades);

    const actsDia = actividades.filter(a => a.fecha === fecha);
    const fechaFormateada = new Date(fecha + "T12:00:00").toLocaleDateString("es-ES", {
        weekday: "long", day: "numeric", month: "long"
    });

    document.getElementById("lista-fecha-titulo").textContent =
        `Actividades — ${fechaFormateada.charAt(0).toUpperCase() + fechaFormateada.slice(1)}`;

    const lista = document.getElementById("lista-actividades");
    if (actsDia.length === 0) {
        lista.innerHTML = "<p style='opacity:0.4; font-size:0.9rem;'>No hay actividades para este día.</p>";
        return;
    }

    const hoy = new Date().toISOString().split("T")[0];

    lista.innerHTML = actsDia.map(a => {
        const puedeIniciar = fecha === hoy && a.estado === "Pendiente";
        const enProgreso   = a.estado === "En progreso";
        return `
        <div class="actividad-item" id="act-item-${a.id}">
            <div class="actividad-info">
                <span class="actividad-nombre">${a.nombre}</span>
                <span class="actividad-meta">${a.categoria} · ${a.duracion} min · ${a.prioridad}</span>
            </div>
            <div class="actividad-acciones">
                <span class="badge badge-${a.estado === 'Completada' ? 'baja' : a.estado === 'En progreso' ? 'media' : 'alta'}">${a.estado}</span>
                ${puedeIniciar ? `<button class="timer-btn-completar" onclick="iniciarActividad(${a.id}, '${a.nombre}', ${a.duracion})">▶ Iniciar</button>` : ""}
                ${enProgreso   ? `<button class="timer-btn-completar" onclick="completarActividad()">✓ Completé</button>` : ""}
                <button class="btn-eliminar" onclick="eliminarActividad(${a.id})">✕</button>
            </div>
        </div>`;
    }).join("");
}

function cambiarMes(delta) {
    mesActual += delta;
    if (mesActual > 11) { mesActual = 0;  anioActual++; }
    if (mesActual < 0)  { mesActual = 11; anioActual--; }
    renderCalendario(todasActividades);
}

async function cargarActividades() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) return;
    try {
        const respuesta = await fetch(`/api/actividades/${usuarioId}`);
        const actividades = await respuesta.json();
        todasActividades = actividades;
        renderCalendario(actividades);
        const hoy = new Date().toISOString().split("T")[0];
        seleccionarDia(hoy, actividades);
    } catch (error) {
        console.error("Error cargando actividades:", error);
    }
}

// ==================== TEMPORIZADOR ====================
let timerInterval = null;
let actividadEnCurso = null;
let timerPausado = false;
let segundosPausados = 0;
let tiempoAlPausar = null;


async function iniciarActividad(id, nombre, duracion) {
    const usuarioId = localStorage.getItem("usuario_id");
    try {
        const res = await fetch(`/api/actividades/${id}/${usuarioId}/iniciar`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" }
        });
        if (!res.ok) { mostrarToast("Error al iniciar actividad"); return; }
        actividadEnCurso = { id, nombre, duracion, horaInicio: new Date() };
        timerPausado = false;
        segundosPausados = 0;
        arrancarTimer();
        cargarActividades();
        mostrarToast(`Iniciaste: ${nombre}`);
    } catch (error) {
        console.error(error);
        mostrarToast("Error de conexión");
    }
}

function arrancarTimer() {
    if (!actividadEnCurso) return;
    document.getElementById("timer-flotante").style.display = "block";
    document.getElementById("timer-nombre").textContent = actividadEnCurso.nombre;
    document.getElementById("timer-pausas-label").style.display = "none";

    if (timerInterval) clearInterval(timerInterval);

    timerInterval = setInterval(() => {
        if (timerPausado) return; // congelado mientras pausa

        const transcurridos = Math.floor((new Date() - actividadEnCurso.horaInicio) / 1000) - segundosPausados;
        const totalSegundos = actividadEnCurso.duracion * 60;
        const restantes = totalSegundos - transcurridos;

        if (restantes <= 0) {
            clearInterval(timerInterval);
            document.getElementById("timer-tiempo").textContent = "¡Tiempo!";
            document.getElementById("timer-barra").style.width = "0%";
            mostrarToast("⏰ Se acabó el tiempo de tu actividad");
            return;
        }

        const mins = Math.floor(restantes / 60);
        const segs = restantes % 60;
        document.getElementById("timer-tiempo").textContent =
            `${String(mins).padStart(2,"0")}:${String(segs).padStart(2,"0")}`;

        const porcentaje = (restantes / totalSegundos) * 100;
        const barra = document.getElementById("timer-barra");
        barra.style.width = porcentaje + "%";
        barra.style.background = porcentaje > 50 ? "#4CB8A4" : porcentaje > 20 ? "#FBBF24" : "#EF4444";
    }, 1000);
}

async function pausarReanudarActividad() {
    if (!actividadEnCurso) return;
    const usuarioId = localStorage.getItem("usuario_id");
    const btnPausar = document.getElementById("btn-pausar");
    const labelPausa = document.getElementById("timer-pausas-label");

    if (!timerPausado) {
        // PAUSAR
        try {
            const res = await fetch(`/api/actividades/${actividadEnCurso.id}/${usuarioId}/pausar`, {
                method: "PUT", headers: { "Content-Type": "application/json" }
            });
            if (!res.ok) { mostrarToast("Error al pausar"); return; }
            timerPausado = true;
            tiempoAlPausar = new Date();
            btnPausar.textContent = "▶ Reanudar";
            btnPausar.style.background = "#334155";
            labelPausa.style.display = "block";
            mostrarToast("⏸ Actividad pausada");
        } catch (e) { console.error(e); }
    } else {
        // REANUDAR
        try {
            const res = await fetch(`/api/actividades/${actividadEnCurso.id}/${usuarioId}/reanudar`, {
                method: "PUT", headers: { "Content-Type": "application/json" }
            });
            if (!res.ok) { mostrarToast("Error al reanudar"); return; }
            const data = await res.json();
            segundosPausados += (data.duracion_pausa || 0);
            timerPausado = false;
            tiempoAlPausar = null;
            btnPausar.textContent = "⏸ Pausar";
            btnPausar.style.background = "";
            labelPausa.style.display = "none";
            mostrarToast("▶ Actividad reanudada");
        } catch (e) { console.error(e); }
    }
}

async function completarActividad() {
    if (!actividadEnCurso) return;
    const usuarioId = localStorage.getItem("usuario_id");

    // Si está pausado, reanudar primero para cerrar la pausa en BD
    if (timerPausado) {
        await fetch(`/api/actividades/${actividadEnCurso.id}/${usuarioId}/reanudar`, {
            method: "PUT", headers: { "Content-Type": "application/json" }
        });
    }

    await fetch(`/api/actividades/${actividadEnCurso.id}/${usuarioId}/finalizar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estado: "Completada", notas: null })
    });

    clearInterval(timerInterval);
    document.getElementById("timer-flotante").style.display = "none";
    timerPausado = false;
    segundosPausados = 0;
    mostrarToast("✅ ¡Actividad completada!");
    actividadEnCurso = null;
    cargarActividades();

    const [resPerfil, resActs] = await Promise.all([
        fetch(`/api/perfil/${usuarioId}`),
        fetch(`/api/actividades/${usuarioId}`)
    ]);
    cargarInicio(await resPerfil.json(), await resActs.json());
}

function noCompletarActividad() {
    if (!actividadEnCurso) return;
    const modal = document.createElement("div");
    modal.className = "modal-incumplida";
    modal.id = "modal-incumplida";
    modal.innerHTML = `
        <div class="modal-incumplida-card">
            <h3>😟 ¿Por qué no completaste la actividad?</h3>
            <p>Tu explicación nos ayuda a entender tu situación y ajustar tu nivel de estrés correctamente.</p>
            <textarea id="explicacion-texto" placeholder="Ej: Tuve una emergencia, me sentí muy cansado, se me olvidó..."></textarea>
            <div class="modal-incumplida-acciones">
                <button class="btn-secundario" onclick="cerrarModalIncumplida()">Cancelar</button>
                <button class="btn-principal" onclick="enviarExplicacion()">Enviar</button>
            </div>
        </div>`;
    document.body.appendChild(modal);
}

async function enviarExplicacion() {
    const explicacion = document.getElementById("explicacion-texto").value.trim();
    if (!explicacion) { mostrarToast("Por favor escribe una explicación"); return; }
    const usuarioId = localStorage.getItem("usuario_id");

    if (timerPausado) {
        await fetch(`/api/actividades/${actividadEnCurso.id}/${usuarioId}/reanudar`, {
            method: "PUT", headers: { "Content-Type": "application/json" }
        });
    }

    await fetch(`/api/actividades/${actividadEnCurso.id}/${usuarioId}/finalizar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estado: "Pendiente", notas: explicacion })
    });

    clearInterval(timerInterval);
    document.getElementById("timer-flotante").style.display = "none";
    timerPausado = false;
    segundosPausados = 0;
    cerrarModalIncumplida();
    mostrarToast("Explicación registrada");
    actividadEnCurso = null;
    cargarActividades();
}

function cerrarModalIncumplida() {
    const modal = document.getElementById("modal-incumplida");
    if (modal) modal.remove();
}

async function verificarActividadEnCurso() {
    const usuarioId = localStorage.getItem("usuario_id");
    try {
        const res = await fetch(`/api/actividades/${usuarioId}/en-curso`);
        const data = await res.json();
        if (data.en_curso) {
            actividadEnCurso = {
                id: data.id,
                nombre: data.nombre,
                duracion: data.duracion,
                horaInicio: new Date(data.hora_inicio)
            };
            timerPausado = false;
            segundosPausados = 0;
            arrancarTimer();
        }
    } catch (error) { console.error(error); }
}

// ==================== HISTORIAL ====================
let historialCompleto = [];
let histMesActual = new Date().getMonth();
let histAnioActual = new Date().getFullYear();
let histDiaSeleccionado = null;

async function cargarHistorial() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) return;

    try {
        const res = await fetch(`/api/actividades/${usuarioId}/historial`);
        if (!res.ok) throw new Error("Error al cargar historial");
        historialCompleto = await res.json();
        renderCalendarioHistorial();

        // Seleccionar hoy por defecto si tiene actividades
        const hoy = new Date().toISOString().split("T")[0];
        const tieneHoy = historialCompleto.some(a => a.fecha === hoy);
        if (tieneHoy) seleccionarDiaHistorial(hoy);

    } catch (e) {
        console.error(e);
    }
}

function renderCalendarioHistorial() {
    const meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                   "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];

    const titulo = document.getElementById("hist-cal-titulo");
    if (!titulo) return;
    titulo.textContent = `${meses[histMesActual]} ${histAnioActual}`;

    const grid = document.getElementById("hist-calendario-grid");
    grid.innerHTML = "";

    const primerDia = new Date(histAnioActual, histMesActual, 1).getDay();
    const diasEnMes = new Date(histAnioActual, histMesActual + 1, 0).getDate();
    const fechaHoyStr = new Date().toISOString().split("T")[0];

    // Celdas vacías
    for (let i = 0; i < primerDia; i++) {
        const vacio = document.createElement("div");
        vacio.className = "cal-dia vacio";
        grid.appendChild(vacio);
    }

    for (let d = 1; d <= diasEnMes; d++) {
        const fecha = `${histAnioActual}-${String(histMesActual+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
        const actsDia = historialCompleto.filter(a => a.fecha === fecha);

        const div = document.createElement("div");
        div.className = "cal-dia";
        if (fecha === fechaHoyStr)       div.classList.add("hoy");
        if (fecha === histDiaSeleccionado) div.classList.add("seleccionado");

        // Dots
        let dotsHTML = "";
        if (actsDia.length > 0) {
            const completadas = actsDia.filter(a => a.estado === "Completada").length;
            const pendientes  = actsDia.filter(a => a.estado === "Pendiente").length;
            const enProgreso  = actsDia.filter(a => a.estado === "En progreso").length;
            dotsHTML = '<div class="cal-dots">';
            if (completadas > 0) dotsHTML += `<div class="cal-dot dot-completada"></div>`;
            if (enProgreso  > 0) dotsHTML += `<div class="cal-dot dot-parcial"></div>`;
            if (pendientes  > 0) dotsHTML += `<div class="cal-dot dot-pendiente"></div>`;
            dotsHTML += '</div>';
        }

        // Número del día con total de actividades si tiene
        div.innerHTML = `<span>${d}</span>${dotsHTML}`;
        if (actsDia.length > 0) {
            div.onclick = () => seleccionarDiaHistorial(fecha);
        } else {
            div.style.opacity = "0.35";
            div.style.cursor = "default";
        }

        grid.appendChild(div);
    }
}

function cambiarMesHistorial(delta) {
    histMesActual += delta;
    if (histMesActual > 11) { histMesActual = 0;  histAnioActual++; }
    if (histMesActual < 0)  { histMesActual = 11; histAnioActual--; }
    histDiaSeleccionado = null;
    document.getElementById("hist-dia-panel").style.display = "none";
    renderCalendarioHistorial();
}

function seleccionarDiaHistorial(fecha) {
    histDiaSeleccionado = fecha;
    renderCalendarioHistorial();

    const actsDia = historialCompleto.filter(a => a.fecha === fecha);
    if (actsDia.length === 0) return;

    const panel = document.getElementById("hist-dia-panel");
    panel.style.display = "block";
    cerrarDetalle();

    // Título del día
    const fechaFormateada = new Date(fecha + "T12:00:00").toLocaleDateString("es-ES", {
        weekday: "long", day: "numeric", month: "long"
    });
    document.getElementById("hist-dia-titulo").textContent =
        fechaFormateada.charAt(0).toUpperCase() + fechaFormateada.slice(1);

    // Estadísticas del día
    const completadas   = actsDia.filter(a => a.estado === "Completada").length;
    const pendientes    = actsDia.filter(a => a.estado === "Pendiente").length;
    const enProgreso    = actsDia.filter(a => a.estado === "En progreso").length;
    const enTiempo      = actsDia.filter(a => a.completada_en_tiempo === true).length;
    const totalPausas   = actsDia.reduce((s, a) => s + (parseInt(a.num_pausas) || 0), 0);
    const minsTotales   = actsDia.reduce((s, a) => s + (a.duracion || 0), 0);

    document.getElementById("hist-dia-stats").innerHTML = `
        <div class="hist-stats-grid">
            <div class="hist-stat-card">
                <div class="hist-stat-valor">${actsDia.length}</div>
                <div class="hist-stat-label">Total actividades</div>
            </div>
            <div class="hist-stat-card stat-verde">
                <div class="hist-stat-valor">${completadas}</div>
                <div class="hist-stat-label">Completadas</div>
            </div>
            <div class="hist-stat-card stat-amarillo">
                <div class="hist-stat-valor">${pendientes}</div>
                <div class="hist-stat-label">Pendientes</div>
            </div>
            <div class="hist-stat-card stat-azul">
                <div class="hist-stat-valor">${enTiempo}</div>
                <div class="hist-stat-label">En tiempo</div>
            </div>
            <div class="hist-stat-card stat-gris">
                <div class="hist-stat-valor">${totalPausas}</div>
                <div class="hist-stat-label">Pausas totales</div>
            </div>
            <div class="hist-stat-card stat-teal">
                <div class="hist-stat-valor">${minsTotales}m</div>
                <div class="hist-stat-label">Minutos planificados</div>
            </div>
        </div>`;

    // Lista de actividades del día
    document.getElementById("hist-dia-lista").innerHTML = actsDia.map(a => {
        const iconoEstado = a.estado === "Completada" ? "✅"
            : a.estado === "En progreso" ? "⏱" : "⏳";

        const tiempoReal = a.hora_inicio && a.hora_fin
            ? calcularTiempoReal(a.hora_inicio, a.hora_fin, a.tiempo_pausas || 0)
            : null;

        const enTiempoTag = a.completada_en_tiempo !== null && a.completada_en_tiempo !== undefined
            ? `<span class="hist-tag ${a.completada_en_tiempo ? 'tag-ok' : 'tag-tarde'}">${a.completada_en_tiempo ? "En tiempo" : "Fuera de tiempo"}</span>`
            : "";

        const pausasTag = a.num_pausas > 0
            ? `<span class="hist-tag tag-pausas">⏸ ${a.num_pausas} pausa${a.num_pausas > 1 ? "s" : ""}</span>`
            : "";

        return `
        <div class="hist-item" onclick="verDetalleActividad(${a.id})">
            <div class="hist-item-izq">
                <span class="hist-icono">${iconoEstado}</span>
                <div>
                    <div class="hist-nombre">${escapeHtml(a.nombre)}</div>
                    <div class="hist-meta">${a.categoria} · ${a.duracion} min estimados · ${a.prioridad}</div>
                    <div class="hist-tags">
                        <span class="badge badge-${a.prioridad === 'Alta' ? 'alta' : a.prioridad === 'Media' ? 'media' : 'baja'}">${a.prioridad}</span>
                        ${enTiempoTag}
                        ${pausasTag}
                    </div>
                </div>
            </div>
            <div class="hist-item-der">
                ${tiempoReal ? `<div class="hist-tiempo-real">${tiempoReal}</div><div class="hist-tiempo-label">tiempo activo</div>` : ""}
                <span class="badge badge-${a.estado === 'Completada' ? 'baja' : a.estado === 'En progreso' ? 'media' : 'alta'}">${a.estado}</span>
            </div>
        </div>`;
    }).join("");

    // Scroll suave al panel
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
}


function filtrarHistorial(filtro, btn) {
    filtroActual = filtro;
    document.querySelectorAll(".filtro-btn").forEach(b => b.classList.remove("activo"));
    if (btn) btn.classList.add("activo");
    renderHistorial();
}

function renderHistorial() {
    const lista = document.getElementById("historial-lista");
    if (!lista) return;

    const datos = filtroActual === "todos"
        ? historialCompleto
        : historialCompleto.filter(a => a.estado === filtroActual);

    if (datos.length === 0) {
        lista.innerHTML = "<p style='opacity:0.4; font-size:0.9rem;'>No hay actividades con este filtro.</p>";
        return;
    }

    lista.innerHTML = datos.map(a => {
        const fechaStr = a.fecha
            ? new Date(a.fecha + "T12:00:00").toLocaleDateString("es-ES", { weekday:"short", day:"numeric", month:"short" })
            : "—";

        const tiempoReal = a.hora_inicio && a.hora_fin
            ? calcularTiempoReal(a.hora_inicio, a.hora_fin, a.tiempo_pausas || 0)
            : null;

        const iconoEstado = a.estado === "Completada" ? "✅"
            : a.estado === "En progreso" ? "⏱"
            : "⏳";

        const enTiempoHTML = a.completada_en_tiempo !== null && a.completada_en_tiempo !== undefined
            ? `<span class="hist-tag ${a.completada_en_tiempo ? 'tag-ok' : 'tag-tarde'}">${a.completada_en_tiempo ? "En tiempo" : "Fuera de tiempo"}</span>`
            : "";

        const pausasHTML = a.num_pausas > 0
            ? `<span class="hist-tag tag-pausas">⏸ ${a.num_pausas} pausa${a.num_pausas > 1 ? "s" : ""}</span>`
            : "";

        return `
        <div class="hist-item" onclick="verDetalleActividad(${a.id})">
            <div class="hist-item-izq">
                <span class="hist-icono">${iconoEstado}</span>
                <div>
                    <div class="hist-nombre">${escapeHtml(a.nombre)}</div>
                    <div class="hist-meta">${a.categoria} · ${fechaStr} · ${a.duracion} min estimados</div>
                    <div class="hist-tags">
                        <span class="badge badge-${a.prioridad === 'Alta' ? 'alta' : a.prioridad === 'Media' ? 'media' : 'baja'}">${a.prioridad}</span>
                        ${enTiempoHTML}
                        ${pausasHTML}
                    </div>
                </div>
            </div>
            <div class="hist-item-der">
                ${tiempoReal ? `<div class="hist-tiempo-real">${tiempoReal}</div><div class="hist-tiempo-label">tiempo activo</div>` : ""}
                <span class="badge badge-${a.estado === 'Completada' ? 'baja' : a.estado === 'En progreso' ? 'media' : 'alta'}">${a.estado}</span>
            </div>
        </div>`;
    }).join("");
}

// Función de seguridad para evitar inyección XSS
function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


function calcularTiempoReal(horaInicio, horaFin, segundosPausas) {
    const inicio = new Date(horaInicio);
    const fin    = new Date(horaFin);
    const totalSeg = Math.floor((fin - inicio) / 1000) - segundosPausas;
    if (totalSeg < 0) return "—";
    const mins = Math.floor(totalSeg / 60);
    const segs = totalSeg % 60;
    return mins > 0 ? `${mins}m ${segs}s` : `${segs}s`;
}

async function verDetalleActividad(actividadId) {
    const usuarioId = localStorage.getItem("usuario_id");
    const panel     = document.getElementById("historial-detalle");
    const contenido = document.getElementById("detalle-contenido");
    panel.style.display = "block";
    contenido.innerHTML = "<p style='opacity:0.4;'>Cargando...</p>";
    panel.scrollIntoView({ behavior: "smooth", block: "start" });

    try {
        const res  = await fetch(`/api/actividades/${actividadId}/${usuarioId}/historial`);
        const data = await res.json();
        const a    = data.actividad;
        const pausas = data.pausas || [];

        const fechaStr = a.fecha
            ? new Date(a.fecha + "T12:00:00").toLocaleDateString("es-ES",
                { weekday:"long", day:"numeric", month:"long", year:"numeric" })
            : "—";

        const horaInicioStr = a.hora_inicio
            ? new Date(a.hora_inicio).toLocaleTimeString("es-ES", { hour:"2-digit", minute:"2-digit" })
            : "—";

        const horaFinStr = a.hora_fin
            ? new Date(a.hora_fin).toLocaleTimeString("es-ES", { hour:"2-digit", minute:"2-digit" })
            : "—";

        const tiempoReal = a.hora_inicio && a.hora_fin
            ? calcularTiempoReal(a.hora_inicio, a.hora_fin, a.tiempo_pausas || 0)
            : "—";

        const pausasHTML = pausas.length === 0
            ? `<p style="opacity:0.4; font-size:0.85rem;">Sin pausas registradas.</p>`
            : pausas.map((p, i) => {
                const ini = new Date(p.hora_pausa).toLocaleTimeString("es-ES",
                    { hour:"2-digit", minute:"2-digit", second:"2-digit" });
                const fin = p.hora_reanudacion
                    ? new Date(p.hora_reanudacion).toLocaleTimeString("es-ES",
                        { hour:"2-digit", minute:"2-digit", second:"2-digit" })
                    : "Aún en pausa";
                const dur = p.duracion_pausa ? `${p.duracion_pausa}s` : "—";
                return `
                <div class="pausa-item">
                    <span class="pausa-num">Pausa ${i + 1}</span>
                    <span>${ini} → ${fin}</span>
                    <span class="pausa-dur">${dur}</span>
                </div>`;
            }).join("");

        document.getElementById("detalle-nombre").textContent = a.nombre;
        contenido.innerHTML = `
        <div class="detalle-grid">
            <div class="detalle-bloque">
                <div class="detalle-fila"><span class="detalle-label">Fecha</span><span>${fechaStr}</span></div>
                <div class="detalle-fila"><span class="detalle-label">Categoría</span><span>${a.categoria}</span></div>
                <div class="detalle-fila"><span class="detalle-label">Prioridad</span><span>${a.prioridad}</span></div>
                <div class="detalle-fila"><span class="detalle-label">Estado</span><span>${a.estado}</span></div>
                ${a.descripcion ? `<div class="detalle-fila"><span class="detalle-label">Descripción</span><span>${a.descripcion}</span></div>` : ""}
            </div>
            <div class="detalle-bloque">
                <div class="detalle-fila"><span class="detalle-label">Duración estimada</span><span>${a.duracion} min</span></div>
                <div class="detalle-fila"><span class="detalle-label">Hora de inicio</span><span>${horaInicioStr}</span></div>
                <div class="detalle-fila"><span class="detalle-label">Hora de fin</span><span>${horaFinStr}</span></div>
                <div class="detalle-fila"><span class="detalle-label">Tiempo activo real</span><span>${tiempoReal}</span></div>
                <div class="detalle-fila"><span class="detalle-label">Tiempo en pausas</span><span>${a.tiempo_pausas ? a.tiempo_pausas + "s" : "0s"}</span></div>
                <div class="detalle-fila">
                    <span class="detalle-label">¿En tiempo?</span>
                    <span>${a.completada_en_tiempo === true ? "✅ Sí" : a.completada_en_tiempo === false ? "⚠️ No" : "—"}</span>
                </div>
            </div>
        </div>
        ${a.notas ? `<div class="detalle-notas"><strong>📝 Nota:</strong> ${a.notas}</div>` : ""}
        <h4 style="margin:1.25rem 0 0.75rem; font-size:0.9rem; color:#94A3B8; text-transform:uppercase; letter-spacing:0.05em;">
            Pausas (${pausas.length})
        </h4>
        <div class="pausas-lista">${pausasHTML}</div>`;

    } catch (e) {
        console.error(e);
        contenido.innerHTML = "<p style='color:#ef4444;'>Error al cargar detalle.</p>";
    }
}


function cerrarDetalle() {
    const panel = document.getElementById("historial-detalle");
    if (panel) panel.style.display = "none";
}


// ==================== ENCUESTA MEJORADA ====================
const encuestaRespuestas = {
    energia: null,
    concentracion: null,
    estado_animo: null,
    presion_percibida: null
};

const encuestaLabels = {
    1: "Muy mal", 2: "Mal", 3: "Regular", 4: "Bien", 5: "Muy bien"
};

function seleccionarEmoji(btn, dimension, valor) {
    // Deseleccionar todos los de esa dimensión
    btn.closest(".encuesta-emojis").querySelectorAll(".emoji-btn")
        .forEach(b => b.classList.remove("seleccionado"));

    // Seleccionar el clickeado
    btn.classList.add("seleccionado");
    encuestaRespuestas[dimension] = valor;

    // Actualizar label
    const labelId = dimension === "presion_percibida"
        ? `val-presion_percibida`
        : `val-${dimension}`;
    const label = document.getElementById(labelId);
    if (label) label.textContent = encuestaLabels[valor];
}

async function enviarEncuesta() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) return;

    const { energia, concentracion, estado_animo, presion_percibida } = encuestaRespuestas;

    if (!energia || !concentracion || !estado_animo || !presion_percibida) {
        mostrarToast("Por favor responde todas las dimensiones");
        return;
    }

    const comentario = document.getElementById("encuesta-comentario")?.value.trim() || "";

    const btnEnviar = document.querySelector("#seccion-encuesta .btn-principal");
    if (btnEnviar) {
        btnEnviar.textContent = "Guardando...";
        btnEnviar.disabled = true;
    }

    try {
        const res = await fetch(`/api/encuesta/${usuarioId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ energia, concentracion, estado_animo, presion_percibida, comentario })
        });

        if (!res.ok) throw new Error("Error al guardar encuesta");

        const badge = document.getElementById("encuesta-badge-estado");
        if (badge) badge.style.display = "inline-block";

        document.getElementById("encuesta-respuesta").textContent =
            "✅ Encuesta registrada correctamente.";

        mostrarToast("Encuesta guardada");

    } catch (e) {
        console.error(e);
        mostrarToast("Error al enviar encuesta");
    } finally {
        if (btnEnviar) {
            btnEnviar.textContent = "Guardar encuesta";
            btnEnviar.disabled = false;
        }
    }
}

async function verificarEncuestaHoy() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) return;

    try {
        const res = await fetch(`/api/encuesta/${usuarioId}/hoy`);
        const data = await res.json();

        if (data.respondida) {
            const badge = document.getElementById("encuesta-badge-estado");
            if (badge) badge.style.display = "inline-block";

            // Marcar los emojis con las respuestas guardadas
            ["energia", "concentracion", "estado_animo", "presion_percibida"].forEach(dim => {
                const valor = data[dim];
                if (!valor) return;
                const contenedor = document.querySelector(`.encuesta-emojis[data-dimension="${dim}"]`);
                if (!contenedor) return;
                const btn = contenedor.querySelector(`[data-valor="${valor}"]`);
                if (btn) {
                    btn.classList.add("seleccionado");
                    encuestaRespuestas[dim] = valor;
                    const label = document.getElementById(`val-${dim}`);
                    if (label) label.textContent = encuestaLabels[valor];
                }
            });

            if (data.comentario) {
                const textarea = document.getElementById("encuesta-comentario");
                if (textarea) textarea.value = data.comentario;
            }

            document.getElementById("encuesta-respuesta").textContent =
                "✅ Ya respondiste la encuesta hoy. Puedes actualizarla si quieres.";
        }
    } catch (e) {
        console.error(e);
    }
}

// ==================== ANÁLISIS ====================
let graficaDias = null;
let graficaCategorias = null;
let graficaBienestar = null;

async function cargarAnalisis() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) return;

    try {
        const res = await fetch(`/api/analisis/${usuarioId}`);
        if (!res.ok) throw new Error("Error al cargar análisis");
        const data = await res.json();
        renderAnalisis(data);
    } catch (e) {
        console.error(e);
    }
}

function renderAnalisis(data) {
    const { fase, actividades_por_dia, categorias, encuestas_semana, stats, patrones, dias } = data;

    // ── Stats rápidos ──
    document.getElementById("an-total-semana").textContent = stats.total_semana;
    document.getElementById("an-completadas-semana").textContent = stats.completadas_semana;
    document.getElementById("an-tasa-semana").textContent = `${stats.tasa_semana}%`;
    document.getElementById("an-fase").textContent = fase.fase;

    // ── Alertas e insights ──
    const alertasDiv = document.getElementById("analisis-alertas");
    const todasAlertas = [...(patrones.alertas || []), ...(patrones.insights || [])];
    alertasDiv.innerHTML = todasAlertas.length === 0 ? "" : todasAlertas.map(a => `
        <div class="alerta-item ${a.tipo === 'danger' ? 'alerta-danger' : a.tipo === 'warning' ? 'alerta-warning' : 'alerta-insight'}">
            <span class="alerta-icono">${a.icono}</span>
            <span>${a.texto}</span>
        </div>
    `).join("");

    // ── Fase de estrés ──
    const badge = document.getElementById("an-fase-badge");
    badge.textContent = fase.fase;
    badge.className = `fase-indicador fase-${fase.fase.toLowerCase()}`;

    const barraFase = document.getElementById("an-fase-barra");
    barraFase.style.width = fase.porcentaje + "%";
    barraFase.style.background = fase.color;

    document.getElementById("an-fase-texto").textContent =
        `Puntuación: ${fase.puntos} — ${getDescripcionFase(fase.fase)}`;

    document.getElementById("an-recomendaciones").innerHTML = fase.recomendaciones.map(rec => `
        <div class="recomendacion-item">
            <div class="rec-icono">${rec.icono}</div>
            <div class="rec-texto">${rec.texto}</div>
        </div>
    `).join("");

    // ── Insights panel ──
    const insightsDiv = document.getElementById("analisis-insights");
    insightsDiv.innerHTML = patrones.insights && patrones.insights.length > 0
        ? patrones.insights.map(i => `
            <div class="recomendacion-item">
                <div class="rec-icono">${i.icono}</div>
                <div class="rec-texto">${i.texto}</div>
            </div>`).join("")
        : "<p style='opacity:0.4; font-size:0.9rem;'>Usa la app unos días más para detectar patrones en tu comportamiento.</p>";

    // ── Gráfica 1: Actividades por día ──
    const labelsDias = dias.map(d =>
        new Date(d + "T12:00:00").toLocaleDateString("es-ES", { weekday: "short", day: "numeric" })
    );

    if (graficaDias) { graficaDias.destroy(); graficaDias = null; }
    graficaDias = new Chart(document.getElementById("grafica-dias").getContext("2d"), {
        type: "bar",
        data: {
            labels: labelsDias,
            datasets: [
                {
                    label: "Completadas",
                    data: actividades_por_dia.map(d => d.completadas),
                    backgroundColor: "#4CB8A4",
                    borderRadius: 6
                },
                {
                    label: "Pendientes",
                    data: actividades_por_dia.map(d => d.pendientes),
                    backgroundColor: "#334155",
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: "#94A3B8", font: { size: 11 } } } },
            scales: {
                x: { stacked: true, ticks: { color: "#64748B" }, grid: { color: "#1E293B" } },
                y: { stacked: true, ticks: { color: "#64748B", stepSize: 1 }, grid: { color: "#1E293B" } }
            }
        }
    });

    // ── Gráfica 2: Categorías (dona) ──
    const catLabels = Object.keys(categorias);
    const catData   = catLabels.map(c => categorias[c].total);
    const catColors = ["#4CB8A4", "#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"];

    if (graficaCategorias) { graficaCategorias.destroy(); graficaCategorias = null; }

    // Limpiar mensajes anteriores del contenedor
    const wrapCat = document.getElementById("grafica-categorias").closest(".perfil-card");
    wrapCat.querySelectorAll(".sin-datos").forEach(p => p.remove());
    document.getElementById("grafica-categorias").style.display = "block";

    if (catLabels.length === 0) {
        document.getElementById("grafica-categorias").style.display = "none";
        const msg = document.createElement("p");
        msg.className = "sin-datos";
        msg.style.cssText = "opacity:0.4; font-size:0.85rem; text-align:center; padding:2rem 0;";
        msg.textContent = "Sin actividades esta semana";
        wrapCat.appendChild(msg);
    } else {
        graficaCategorias = new Chart(document.getElementById("grafica-categorias").getContext("2d"), {
            type: "doughnut",
            data: {
                labels: catLabels,
                datasets: [{
                    data: catData,
                    backgroundColor: catColors.slice(0, catLabels.length),
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                cutout: "65%",
                plugins: {
                    legend: {
                        position: "right",
                        labels: { color: "#94A3B8", font: { size: 11 }, padding: 12 }
                    }
                }
            }
        });
    }

    // ── Gráfica 3: Bienestar (líneas) ──
    const encConDatos = encuestas_semana.filter(e => e.energia !== null);

    if (graficaBienestar) { graficaBienestar.destroy(); graficaBienestar = null; }

    // Limpiar mensajes anteriores
    const wrapBienestar = document.getElementById("grafica-bienestar").closest(".perfil-card");
    wrapBienestar.querySelectorAll(".sin-datos").forEach(p => p.remove());
    document.getElementById("grafica-bienestar").style.display = "block";

    if (encConDatos.length < 2) {
        document.getElementById("grafica-bienestar").style.display = "none";
        const msg = document.createElement("p");
        msg.className = "sin-datos";
        msg.style.cssText = "opacity:0.4; font-size:0.85rem; text-align:center; padding:1.5rem 0;";
        msg.textContent = "Responde la encuesta diaria al menos 2 días para ver tu evolución de bienestar.";
        wrapBienestar.appendChild(msg);
    } else {
        const labelsEnc = encuestas_semana.map(e =>
            new Date(e.fecha + "T12:00:00").toLocaleDateString("es-ES", { weekday: "short", day: "numeric" })
        );

        graficaBienestar = new Chart(document.getElementById("grafica-bienestar").getContext("2d"), {
            type: "line",
            data: {
                labels: labelsEnc,
                datasets: [
                    {
                        label: "⚡ Energía",
                        data: encuestas_semana.map(e => e.energia),
                        borderColor: "#4CB8A4",
                        backgroundColor: "rgba(76,184,164,0.1)",
                        tension: 0.4, fill: true, pointRadius: 4, spanGaps: true
                    },
                    {
                        label: "🧠 Concentración",
                        data: encuestas_semana.map(e => e.concentracion),
                        borderColor: "#3B82F6",
                        backgroundColor: "rgba(59,130,246,0.05)",
                        tension: 0.4, fill: false, pointRadius: 4, spanGaps: true
                    },
                    {
                        label: "💆 Ánimo",
                        data: encuestas_semana.map(e => e.estado_animo),
                        borderColor: "#F59E0B",
                        backgroundColor: "rgba(245,158,11,0.05)",
                        tension: 0.4, fill: false, pointRadius: 4, spanGaps: true
                    },
                    {
                        label: "🔥 Presión",
                        data: encuestas_semana.map(e => e.presion_percibida),
                        borderColor: "#EF4444",
                        backgroundColor: "rgba(239,68,68,0.05)",
                        tension: 0.4, fill: false, pointRadius: 4, spanGaps: true
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: "#94A3B8", font: { size: 11 } } } },
                scales: {
                    x: { ticks: { color: "#64748B" }, grid: { color: "#1E293B" } },
                    y: {
                        min: 1, max: 5,
                        ticks: {
                            color: "#64748B",
                            stepSize: 1,
                            callback: v => ["", "Muy mal", "Mal", "Regular", "Bien", "Muy bien"][v] || v
                        },
                        grid: { color: "#1E293B" }
                    }
                }
            }
        });
    }
}

function mostrarModalVerificacion(mensaje) {
    document.getElementById("modalTitulo").innerText = "Cuenta no verificada";
    document.getElementById("modalMensaje").innerText = mensaje;
    
    // Agregar botón de verificar al modal
    const btnCerrar = document.querySelector(".btn-cerrar");
    btnCerrar.innerHTML = `
        <label for="btn-modal" onclick="irAVerificar()">Verificar ahora</label>
        <label for="btn-modal" style="margin-left:8px; background:#334155;">Cerrar</label>
    `;
    document.getElementById("btn-modal").checked = true;
}

function irAVerificar() {
    const usuarioId = localStorage.getItem("usuario_id_temp");
    if (!usuarioId) {
        alert("No se pudo obtener el usuario. Regístrate de nuevo.");
        return;
    }
    window.location.href = `verificar.html?id=${usuarioId}&tipo=registro`;
}
