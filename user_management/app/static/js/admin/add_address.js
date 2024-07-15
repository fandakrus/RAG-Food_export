async function submitForm(event) {
    event.preventDefault();
    const formData = new FormData();

    const fileInput = document.getElementById('file');
    const emailsInput = document.getElementById('emails');
    const responseMessage = document.getElementById('response-message');
    const responseText = document.getElementById('response-text');

    if (fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
    } else if (emailsInput.value.trim() !== '') {
        formData.append('emails', emailsInput.value.trim());
    } else {
        responseText.textContent = "Please select a file or enter email addresses";
        responseMessage.style.color = 'red';
        responseMessage.style.backgroundColor = 'pink';
        responseMessage.style.display = 'flex';
        return;
    }

    try {
        const response = await fetch('/admin/add_address', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (data.success) {
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
    } catch (error) {
        responseText.textContent = error.message;
        responseMessage.style.color = 'red';
        responseMessage.style.backgroundColor = 'pink';
        responseMessage.style.display = 'flex';
    }
}

function closeResponseMessage() {
    document.getElementById('response-message').style.display = 'none';
}