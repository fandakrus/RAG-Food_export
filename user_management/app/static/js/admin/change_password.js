document.getElementById('change-password-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const userId = window.location.pathname.split('/').pop();
    const url = `/admin/change_password/${userId}`;

    const formData = {
        new_password: document.getElementById('new_password').value,
        confirm_password: document.getElementById('confirm_password').value
    };

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        const responseMessage = document.getElementById('response-message');
        if (data.status === 'success') {
            responseMessage.textContent = data.message;
            responseMessage.style.color = 'green';
            responseMessage.style.display = 'block';
        } else {
            responseMessage.textContent = data.message;
            responseMessage.style.color = 'red';
            responseMessage.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});