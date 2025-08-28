/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │           FRONTEND SCRIPTS          │
 *  └─────────────────────────────────────┘
 *  JavaScript functionality for Finance Insights web app
 * 
 *  Provides client-side functionality including delete operations,
 *  form validation, and interactive UI enhancements.
 */

// Delete insight function
async function deleteInsight(insightId, redirectToHome = false) {
    if (!confirm('Are you sure you want to delete this insight? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/insight/${insightId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            if (redirectToHome) {
                window.location.href = '/';
            } else {
                // Remove the card from the DOM with animation
                const card = document.querySelector(`[data-insight-id="${insightId}"]`)?.closest('.col-md-6, .col-lg-4');
                if (card) {
                    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(-20px)';
                    setTimeout(() => card.remove(), 300);
                }
                
                showNotification('Insight deleted successfully', 'success');
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to delete insight', 'error');
        }
    } catch (error) {
        console.error('Error deleting insight:', error);
        showNotification('Network error occurred', 'error');
    }
}

// Show notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Form validation enhancement
document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Enhanced form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields', 'error');
            }
        });

        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.hasAttribute('required')) {
                    if (!this.value.trim()) {
                        this.classList.add('is-invalid');
                        this.classList.remove('is-valid');
                    } else {
                        this.classList.remove('is-invalid');
                        this.classList.add('is-valid');
                    }
                }
            });
        });
    });

    // Image URL preview
    const imageUrlInput = document.getElementById('imageURL');
    if (imageUrlInput) {
        imageUrlInput.addEventListener('blur', function() {
            const url = this.value.trim();
            if (url) {
                // Create preview if it doesn't exist
                let preview = document.getElementById('image-preview');
                if (!preview) {
                    preview = document.createElement('div');
                    preview.id = 'image-preview';
                    preview.className = 'mt-2';
                    this.parentNode.appendChild(preview);
                }

                preview.innerHTML = `
                    <img src="${url}" class="img-thumbnail" style="max-width: 200px; max-height: 150px;" 
                         onerror="this.parentNode.innerHTML='<small class=\\'text-danger\\'>Invalid image URL</small>'"
                         alt="Image preview">
                `;
            } else {
                const preview = document.getElementById('image-preview');
                if (preview) {
                    preview.remove();
                }
            }
        });
    }

    // Confidence slider enhancement
    const confidenceInput = document.getElementById('AIConfidence');
    if (confidenceInput) {
        confidenceInput.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                const percentage = Math.round(value * 100);
                let label = document.getElementById('confidence-label');
                if (!label) {
                    label = document.createElement('small');
                    label.id = 'confidence-label';
                    label.className = 'form-text text-muted';
                    this.parentNode.appendChild(label);
                }
                label.textContent = `${percentage}% confidence`;
            }
        });
    }
});

// Utility function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Search functionality (can be enhanced later)
function searchInsights(query) {
    const cards = document.querySelectorAll('.card');
    const searchTerm = query.toLowerCase();

    cards.forEach(card => {
        const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
        const content = card.querySelector('.card-text')?.textContent.toLowerCase() || '';
        const type = card.querySelector('.badge')?.textContent.toLowerCase() || '';

        if (title.includes(searchTerm) || content.includes(searchTerm) || type.includes(searchTerm)) {
            card.closest('.col-md-6, .col-lg-4').style.display = 'block';
        } else {
            card.closest('.col-md-6, .col-lg-4').style.display = 'none';
        }
    });
}
