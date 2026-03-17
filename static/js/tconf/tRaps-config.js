$(document).ready(function() {
    $('#tablaRaps').DataTable({
        // 1. Activar extensiones
        responsive: true,
        deferRender: true, // Requerido para Scroller
        scrollY: 400,      // Alto fijo de la tabla (Scroller)
        scrollCollapse: true,
        scroller: true,

        // 2. DOM (Estructura de Bootstrap 5 para acomodar botones y buscador)
        // B = Botones, f = Filtro, r = Procesando, t = Tabla, i = Info
        dom: "<'row mb-3'<'col-sm-12 col-md-6'B><'col-sm-12 col-md-6 d-flex justify-content-end'f>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row mt-3'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'>>", 
             // Nota: Quitamos la "p" (paginación) del DOM porque estás usando Scroller (scroll infinito)

        // 3. Configuración de los botones de exportación
        buttons: [
            {
                extend: 'excelHtml5',
                text: '📄 Excel',
                className: 'btn btn-success btn-sm me-2',
                exportOptions: { columns: [0, 1] } // Exporta solo Competencia y RAP (no Acciones)
            },
            {
                extend: 'pdfHtml5',
                text: '📕 PDF',
                className: 'btn btn-danger btn-sm',
                exportOptions: { columns: [0, 1] }
            }
        ],

        // 4. Desactivar ordenamiento en la columna de botones
        columnDefs: [
            { orderable: false, targets: 2 } // La columna 2 es la de "Acciones"
        ],

        // 5. Idioma (mantenemos tu configuración offline adaptada a RAPs)
        language: {
            "sProcessing":     "Procesando...",
            "sLengthMenu":     "Mostrar _MENU_ registros",
            "sZeroRecords":    "No se encontraron resultados",
            "sEmptyTable":     "Ningún RAP registrado en esta ficha todavía",
            "sInfo":           "Mostrando _START_ a _END_ de _TOTAL_ RAPs",
            "sInfoEmpty":      "Mostrando 0 RAPs",
            "sInfoFiltered":   "(filtrado de _MAX_ RAPs)",
            "sSearch":         "Buscar:",
        }
    });
});