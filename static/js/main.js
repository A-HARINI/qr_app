// Main JavaScript file for QR App

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(msg) {
        setTimeout(function() {
            msg.style.transition = 'opacity 0.5s';
            msg.style.opacity = '0';
            setTimeout(function() {
                msg.remove();
            }, 500);
        }, 5000);
    });
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#dc3545';
                } else {
                    field.style.borderColor = '#e0e0e0';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields');
            }
        });
    });
});

// Add to cart function
function addToCart(event, productId) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    formData.append('product_id', productId);
    
    fetch('/add_to_cart', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            form.reset();
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error adding to cart');
    });
}

// Notify me function
function notifyMe(event, productId) {
    event.preventDefault();
    const formData = new FormData();
    formData.append('product_id', productId);
    
    fetch('/notify_me', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('You will be notified when this product is back in stock!');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error submitting notification request');
    });
}





























