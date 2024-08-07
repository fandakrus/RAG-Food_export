function editUser(userId) {
    window.location.href = `/admin/edit_user/${userId}`;
}

function deleteUser(userId) {
    if (confirm("Are you sure you want to delete this user?")) {
        fetch(`/admin/delete_user/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}'
            }
        })
        .then(response => response.text())
        .then(text => {
            return JSON.parse(text);
        })
        .then(data => {
            if (data.status === 'success') {
                alert(data.message);
                location.reload();
            } else {
                alert(data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

function changePassword(userId) {
    window.location.href = `/admin/change_password/${userId}`;
}

function resetPassword(userId) {
    if (confirm("Are you sure you want to reset password for this user?")) {
        fetch(`/admin/reset_password/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}'
            }
        })
        .then(response => response.text())
        .then(text => {
            return JSON.parse(text);
        })
        .then(data => {
            if (data.status === 'success') {
                alert(data.message);
                location.reload();
            } else {
                alert(data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

function navigateToPage(page) {
    window.location.href = `/admin/users?page=${page}`;
}