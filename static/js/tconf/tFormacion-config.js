$(document).ready(function() {
    $('#tablaFormacion').DataTable({
        // 1. Activar extensiones
        responsive: true,
        deferRender: true, // Requerido para Scroller
        scrollY: 400,      // Alto fijo de la tabla (Scroller)
        scrollCollapse: true,
        scroller: true,

        // 2. DOM (Estructura de Bootstrap 5 para acomodar botones y buscador)
        dom: "<'row mb-3'<'col-sm-12 col-md-6'B><'col-sm-12 col-md-6 d-flex justify-content-end'f>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row mt-3'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'>>", 

        // 3. Configuración de los botones de exportación
        buttons: [
            {
                extend: 'excelHtml5',
                text: '<i class="bi bi-file-earmark-excel"></i> Excel',
                className: 'btn btn-success btn-sm me-2 shadow-sm',
                // Exporta: Fase (0), Actividad (1), RAPs (2), Fechas (3), Estado (4)
                exportOptions: { columns: [0, 1, 2, 3, 4] } 
            },
            {
                extend: 'pdfHtml5',
                text: '<i class="bi bi-file-earmark-pdf"></i> PDF',
                className: 'btn btn-danger btn-sm shadow-sm',
                exportOptions: { columns: [0, 1, 2, 3, 4] }
            }
        ],

        // 4. Desactivar ordenamiento en la columna de botones (índice 5 es "Acciones")
        columnDefs: [
            { orderable: false, targets: 5 }
        ],

        // 5. Idioma (Adaptado al contexto de Actividades)
        language: {
            "sProcessing":     "Procesando...",
            "sLengthMenu":     "Mostrar _MENU_ registros",
            "sZeroRecords":    "No se encontraron resultados",
            "sEmptyTable":     "Ninguna actividad registrada en el cronograma todavía",
            "sInfo":           "Mostrando _START_ a _END_ de _TOTAL_ actividades",
            "sInfoEmpty":      "Mostrando 0 actividades",
            "sInfoFiltered":   "(filtrado de un total de _MAX_ actividades)",
            "sSearch":         "Buscar:",
        }
    });
});