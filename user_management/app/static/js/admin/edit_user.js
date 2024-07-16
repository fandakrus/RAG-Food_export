document.getElementById('edit-user-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const userId = window.location.pathname.split('/').pop();
    const url = `/admin/edit_user/${userId}`;

    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        role: document.getElementById('role').value,
        email_verified: document.getElementById('email_verified').checked
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
        const responseText = document.getElementById('response-text');
        if (data.status === 'success') {
            responseText.textContent = data.message;
            responseMessage.style.color = 'green';
            responseMessage.style.backgroundColor = 'lightgreen';
            responseMessage.style.display = 'flex';
        } else {
            responseText.textContent = data.message;
            responseMessage.style.color = 'red';
            responseMessage.style.backgroundColor = 'pink';
            responseMessage.style.display = 'flex';
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

function closeResponseMessage() {
    document.getElementById('response-message').style.display = 'none';
}