document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/admin/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email, password: password })
    });

    const result = await response.json();
    const responseMessage = document.getElementById('responseMessage');

    if (response.ok) {
        responseMessage.textContent = result.message;
        responseMessage.style.display = 'block';
        responseMessage.style.color = 'green';
        window.location.href = result.redirect;
    } else {
        responseMessage.textContent = result.message;
        responseMessage.style.display = 'block';
        responseMessage.style.color = 'red';
    }
});