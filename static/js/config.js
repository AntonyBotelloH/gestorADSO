document.addEventListener('DOMContentLoaded', () => {
    console.log("Archivo config.js cargado correctamente.");

    // ==========================================
    // 1. MODO OSCURO (TEMAS VISUALES)
    // ==========================================
    const temaRadios = document.querySelectorAll('input[name="temaVisual"]');
    // Bootstrap 5 aplica el tema al html, no al body
    const htmlElement = document.documentElement; 

    // Cargar el tema guardado
    const temaGuardado = localStorage.getItem('temaSena') || 'light';
    htmlElement.setAttribute('data-bs-theme', temaGuardado);
    
    // Marcar el radio button correcto
    if (temaGuardado === 'dark') {
        const btnOscuro = document.getElementById('temaOscuro');
        if(btnOscuro) btnOscuro.checked = true;
    } else {
        const btnOficial = document.getElementById('temaOficial');
        if(btnOficial) btnOficial.checked = true;
    }

    // Escuchar cambios
    temaRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const nuevoTema = e.target.id === 'temaOscuro' ? 'dark' : 'light';
            htmlElement.setAttribute('data-bs-theme', nuevoTema);
            localStorage.setItem('temaSena', nuevoTema); 
            console.log("Tema cambiado a:", nuevoTema);
        });
    });

    // ==========================================
    // 2. ALTO CONTRASTE
    // ==========================================
    const switchContraste = document.getElementById('switchContraste');
    const body = document.body;

    const contrasteGuardado = localStorage.getItem('altoContrasteSena') === 'true';
    if(switchContraste) switchContraste.checked = contrasteGuardado;

    // Aplicar contraste inicial si estaba guardado
    if (contrasteGuardado) {
        body.style.filter = 'contrast(150%) saturate(120%)';
        body.style.backgroundColor = '#000';
    }

    if(switchContraste) {
        switchContraste.addEventListener('change', (e) => {
            const activado = e.target.checked;
            if(activado){
                body.style.filter = 'contrast(150%) saturate(120%)';
                body.style.backgroundColor = '#000';
            } else {
                body.style.filter = 'none';
                body.style.backgroundColor = '';
            }
            localStorage.setItem('altoContrasteSena', activado);
            console.log("Alto contraste:", activado);
        });
    }

    // ==========================================
    // 3. TAMAÑO DE TEXTO (ACCESIBILIDAD)
    // ==========================================
    const btnMenos = document.getElementById('btn-txt-menos');
    const btnNormal = document.getElementById('btn-txt-normal');
    const btnMas = document.getElementById('btn-txt-mas');
    
    const sizeGuardado = localStorage.getItem('tamanoTextoSena') || '16';
    htmlElement.style.fontSize = sizeGuardado + 'px';
    actualizarBotonesActivos(sizeGuardado);

    if(btnMenos) btnMenos.addEventListener('click', () => cambiarTamano('14'));
    if(btnNormal) btnNormal.addEventListener('click', () => cambiarTamano('16'));
    if(btnMas) btnMas.addEventListener('click', () => cambiarTamano('18'));

    function cambiarTamano(size) {
        htmlElement.style.fontSize = size + 'px';
        localStorage.setItem('tamanoTextoSena', size);
        actualizarBotonesActivos(size);
        console.log("Tamaño de texto cambiado a:", size);
    }

    function actualizarBotonesActivos(size) {
        if(!btnMenos || !btnNormal || !btnMas) return;

        [btnMenos, btnNormal, btnMas].forEach(btn => {
            btn.classList.remove('btn-secondary', 'active');
            btn.classList.add('btn-outline-secondary');
        });

        if (size === '14') {
            btnMenos.classList.add('btn-secondary', 'active');
            btnMenos.classList.remove('btn-outline-secondary');
        } else if (size === '16') {
            btnNormal.classList.add('btn-secondary', 'active');
            btnNormal.classList.remove('btn-outline-secondary');
        } else if (size === '18') {
            btnMas.classList.add('btn-secondary', 'active');
            btnMas.classList.remove('btn-outline-secondary');
        }
    }
});