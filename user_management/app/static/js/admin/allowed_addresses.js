function deleteUser(userId) {
    if (confirm("Are you sure you want to delete this address?")) {
        fetch(`/admin/delete_address/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Address deleted successfully.");
                location.reload();
            } else {
                alert("Failed to delete address: " + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert("An error occurred while deleting the address.");
        });
    }
}