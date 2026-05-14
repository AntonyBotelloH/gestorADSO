$(document).ready(function () {
    // 1. LÓGICA DE AUTOCOMPLETADO DEL CONCEPTO (Individual)
    const selectElement = document.getElementById('selectConcepto')
    const inputElement = document.getElementById('inputValor')
    
    if (selectElement && inputElement && typeof $.fn.select2 !== 'undefined') {
      $('#selectConcepto').on('select2:select', function (e) {
        const selectedOption = e.params.data.element
        const valorSugerido = selectedOption.getAttribute('data-valor')
        if (valorSugerido) {
          inputElement.value = valorSugerido
        } else {
          inputElement.value = ''
        }
      })
    }

    // 1b. LÓGICA DE AUTOCOMPLETADO DEL CONCEPTO (Masivo)
    const selectMasivoElement = document.getElementById('selectConceptoMasivo')
    const inputMasivoElement = document.getElementById('inputValorMasivo')
    
    if (selectMasivoElement && inputMasivoElement && typeof $.fn.select2 !== 'undefined') {
      $('#selectConceptoMasivo').on('select2:select', function (e) {
        const selectedOption = e.params.data.element
        const valorSugerido = selectedOption.getAttribute('data-valor')
        if (valorSugerido) {
          inputMasivoElement.value = valorSugerido
        } else {
          inputMasivoElement.value = ''
        }
      })
    }

    // 2. INICIALIZACIÓN DE DATATABLES
    $('#tablaMovimientos').DataTable({
        responsive: true,
        deferRender: true,
        scrollY: 400,
        scrollCollapse: true,
        scroller: true,

        // DOM: Botones a la izquierda, buscador a la derecha
        dom: "<'row mb-3'<'col-sm-12 col-md-6'B><'col-sm-12 col-md-6 d-flex justify-content-end'f>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row mt-3'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'>>", 

        buttons: [
            {
                extend: 'excelHtml5',
                text: '📄 Excel',
                className: 'btn btn-success btn-sm me-2',
                exportOptions: { columns: [0, 1, 2, 3, 4] } // Omite Acciones
            },
            {
                extend: 'pdfHtml5',
                text: '📕 PDF',
                className: 'btn btn-danger btn-sm',
                exportOptions: { columns: [0, 1, 2, 3, 4] } // Omite Acciones
            }
        ],

        // Desactivar ordenamiento en la columna "Acciones" (índice 5)
        columnDefs: [
            { orderable: false, targets: 5 }
        ],

        language: {
            "sProcessing":     "Procesando...",
            "sLengthMenu":     "Mostrar _MENU_ registros",
            "sZeroRecords":    "No se encontraron resultados",
            "sEmptyTable":     "Ningún movimiento registrado en esta ficha todavía",
            "sInfo":           "Mostrando _START_ a _END_ de _TOTAL_ movimientos",
            "sInfoEmpty":      "Mostrando 0 movimientos",
            "sInfoFiltered":   "(filtrado de _MAX_ movimientos)",
            "sSearch":         "Buscar:",
        }
    });
  });