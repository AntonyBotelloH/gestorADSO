// Usamos el evento estándar para que cargue bien al abrir la página
    document.addEventListener("DOMContentLoaded", function() {
        
      

        // 2. MAGIA: Escuchamos cuando el usuario seleccione una falta del catálogo
        $('#id_falta_cometida').on('change', function() {
            const faltaId = $(this).val();
            
            // Si deseleccionan (o está vacío), limpiamos los campos
            if (!faltaId) {
                $('#id_tipo_falta').val('');
                $('#id_gravedad').val('');
                return;
            }

            // Consultamos a nuestra API de Django en tiempo real
            fetch(`/llamados/api/falta/${faltaId}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Cambiamos los valores de los selects ocultos
                        $('#id_tipo_falta').val(data.tipo_falta);
                        $('#id_gravedad').val(data.gravedad);
                        
                        // Opcional: Si los campos tipo_falta tuvieran select2, hay que hacer un .trigger('change')
                        // $('#id_tipo_falta').trigger('change'); 
                    } else {
                        console.error('No se pudo encontrar la tipificación de la falta.');
                    }
                })
                .catch(error => console.error("Error consultando la API de faltas:", error));
        });
    });