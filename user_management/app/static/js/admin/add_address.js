async function submitForm(event) {
    event.preventDefault();
    const formData = new FormData();

    const fileInput = document.getElementById('file');
    const emailsInput = document.getElementById('emails');
    const responseMessage = document.getElementById('responseMessage');

    // Clear previous response message
    responseMessage.innerHTML = '';

    if (fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
    } else if (emailsInput.value.trim() !== '') {
        formData.append('emails', emailsInput.value.trim());
    } else {
        responseMessage.innerHTML = '<p style="color: red;">Please provide a file or email addresses.</p>';
        return;
    }

    try {
        const response = await fetch('/admin/add_address', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        if (result.success) {
            responseMessage.innerHTML = '<p style="color: green;">' + result.message + '</p>';
        } else {
            responseMessage.innerHTML = '<p style="color: red;">Error: ' + result.message + '</p>';
        }
    } catch (error) {
        responseMessage.innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
    }
}