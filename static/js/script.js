document.addEventListener("DOMContentLoaded", function() {
    // Get the upload form and button
    const uploadForm = document.getElementById('upload-form');
    const uploadBtn = document.getElementById('upload-btn');
    const progressArea = document.getElementById('upload-progress-area');
    const progressBar = document.getElementById('upload-progress-bar');
    const statusMessage = document.getElementById('upload-status');
    
    if (uploadForm) {
        // Add event listener for form submission
        uploadForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Previene l'invio tradizionale del form
            
            const fileInput = document.getElementById('file');
            
            // Validate that a file is selected
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Per favore seleziona un file ZIP.');
                return;
            }
            
            const file = fileInput.files[0];
            
            // Check file type
            if (!file.name.toLowerCase().endsWith('.zip')) {
                alert('Solo file ZIP sono consentiti.');
                return;
            }
            
            // Show loading state
            uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Elaborazione...';
            uploadBtn.disabled = true;
            
            // Mostra l'area di progresso
            progressArea.classList.remove('d-none');
            
            // Per i file grandi, utilizziamo FormData per inviarli
            const formData = new FormData();
            formData.append('file', file);
            
            // Crea una richiesta AJAX con supporto per la barra di progresso
            const xhr = new XMLHttpRequest();
            
            // Traccia il progresso del caricamento
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    
                    // Aggiorna la barra di progresso
                    progressBar.style.width = percentComplete + '%';
                    progressBar.textContent = percentComplete + '%';
                    progressBar.setAttribute('aria-valuenow', percentComplete);
                    
                    // Aggiorna il messaggio di stato
                    if (percentComplete < 100) {
                        statusMessage.textContent = `Caricamento in corso: ${percentComplete}%`;
                    } else {
                        statusMessage.textContent = 'Caricamento completato. Elaborazione in corso...';
                    }
                }
            });
            
            // Gestisci eventi di completamento e errori
            xhr.addEventListener('load', function() {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.redirect) {
                            // Reindirizza alla pagina di avanzamento o risultati
                            window.location.href = response.redirect;
                        } else {
                            statusMessage.textContent = response.message || 'Elaborazione completata con successo!';
                            // Reindirizza alla pagina dei risultati dopo un breve ritardo
                            setTimeout(() => {
                                window.location.href = '/result';
                            }, 1000);
                        }
                    } catch (e) {
                        // Se la risposta non è JSON (probabilmente HTML), reindirizza direttamente
                        window.location.href = response.redirect || '/progress';
                    }
                } else {
                    // Errore nell'upload o nell'elaborazione
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i> Riprova';
                    progressBar.classList.remove('bg-primary');
                    progressBar.classList.add('bg-danger');
                    statusMessage.textContent = 'Errore durante il caricamento. Riprova.';
                }
            });
            
            xhr.addEventListener('error', function() {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i> Riprova';
                progressBar.classList.remove('bg-primary');
                progressBar.classList.add('bg-danger');
                statusMessage.textContent = 'Errore di rete. Controlla la connessione e riprova.';
            });
            
            xhr.addEventListener('abort', function() {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i> Riprova';
                statusMessage.textContent = 'Caricamento annullato.';
            });
            
            // Invia la richiesta
            xhr.open('POST', uploadForm.action, true);
            // Aggiungi header per far riconoscere la richiesta AJAX
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.send(formData);
        });
    }
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
});
