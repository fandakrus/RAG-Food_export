function validatePasswords() {
    const password = document.querySelector('input[name="password"]').value;
    const confirmPassword = document.querySelector('input[name="confirm_password"]').value;
    const errorMessage = document.getElementById('error-message');

    if (password !== confirmPassword) {
        errorMessage.textContent = 'Error: Passwords do not match.';
        errorMessage.style.display = 'block';
        return false;
    } 

    if (password.length < 8) {
        errorMessage.textContent = 'Error: Password must be at least 8 characters long.';
        errorMessage.style.display = 'block';
        return false;
    }

    errorMessage.style.display = 'none';
    return true;
}


document.getElementById('reset-password-form').addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent the default form submission

    if (!validatePasswords()) {
        return;
    }

    const form = event.target;
    const formData = new FormData(form);
    const errorMessage = document.getElementById('error-message');

    // Convert form data to JSON
    const formDataJson = {};
    formData.forEach((value, key) => {
        formDataJson[key] = value;
    });

    // Clear previous error message
    errorMessage.style.display = 'none';

    try {
        const response = await fetch('/reset_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formDataJson)
        });

        const result = await response.json();

        if (response.ok) {
            // Redirect to email verification page
            window.location.href = '../password_reset_success';
        } else {
            // Display error message
            errorMessage.textContent = `Error: ${result.message}`;
            errorMessage.style.display = 'block';
        }
    } catch (error) {
        // Display error message
        errorMessage.textContent = 'Error: An unexpected error occurred. ' + error.message;
        errorMessage.style.display = 'block';
    }
});