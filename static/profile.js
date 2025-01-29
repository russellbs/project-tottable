document.addEventListener('DOMContentLoaded', function () {
    const childrenList = document.getElementById('children-list');
    const addChildButton = document.getElementById('add-child-btn');
    const addChildFormContainer = document.getElementById('add-child-form');
    const addChildForm = document.getElementById('add-child-form-element');

    // Ensure all essential DOM elements are present
    if (!childrenList || !addChildButton || !addChildForm || !addChildFormContainer) {
        console.error("Essential DOM elements for child management are missing.");
    }

    // Initialize custom multi-select dropdown
    function initializeCustomMultiSelect() {
        const dropdowns = document.querySelectorAll('.custom-multi-select');

        dropdowns.forEach(dropdown => {
            dropdown.addEventListener('click', function () {
                const optionsContainer = dropdown.querySelector('.options-container');
                optionsContainer.style.display =
                    optionsContainer.style.display === 'block' ? 'none' : 'block';
            });

            dropdown.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
                checkbox.addEventListener('change', function () {
                    const selectedContainer = dropdown.querySelector('.selected-options');
                    const selected = Array.from(
                        dropdown.querySelectorAll('input[type="checkbox"]:checked')
                    ).map(input => input.dataset.label);

                    selectedContainer.innerText = selected.length > 0
                        ? selected.join(', ')
                        : 'Select options';
                });
            });
        });

        // Close dropdown if clicked outside
        document.addEventListener('click', function (e) {
            dropdowns.forEach(dropdown => {
                if (!dropdown.contains(e.target)) {
                    const optionsContainer = dropdown.querySelector('.options-container');
                    if (optionsContainer) optionsContainer.style.display = 'none';
                }
            });
        });
    }

    // Call the custom multi-select initialization
    initializeCustomMultiSelect();

    // Show/Hide "Add Child" Form
    addChildButton.addEventListener('click', function () {
        addChildFormContainer.style.display =
            addChildFormContainer.style.display === 'block' ? 'none' : 'block';
    });

    // Handle "Add Child" Form Submission
    addChildForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(addChildForm);

        fetch(addChildForm.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData,
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to add child: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    location.reload(); // Reload the page to show the new child
                } else {
                    console.error('Error adding child:', data.error);
                    alert(data.error || 'Failed to add the child. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                alert('An error occurred while adding the child.');
            });
    });

    // Handle Edit Button Click
    childrenList.addEventListener('click', function (e) {
        if (e.target.classList.contains('edit-child-btn')) {
            const childProfile = e.target.closest('.child-profile');
            const displayDiv = childProfile.querySelector('.child-display');
            const editFormDiv = childProfile.querySelector('.child-edit-form');

            // Show the inline edit form
            displayDiv.style.display = 'none';
            editFormDiv.style.display = 'block';

            // Initialize custom multi-select in the edit form
            initializeCustomMultiSelect();
        }
    });

    // Handle Cancel Button Click
    childrenList.addEventListener('click', function (e) {
        if (e.target.classList.contains('cancel-edit-btn')) {
            const childProfile = e.target.closest('.child-profile');
            const displayDiv = childProfile.querySelector('.child-display');
            const editFormDiv = childProfile.querySelector('.child-edit-form');

            // Revert back to display view
            displayDiv.style.display = 'block';
            editFormDiv.style.display = 'none';
        }
    });

    // Handle Inline Form Submission for Editing
    childrenList.addEventListener('submit', function (e) {
        if (e.target.classList.contains('edit-child-form')) {
            e.preventDefault();
            const form = e.target;
            const childId = form.dataset.childId;

            const formData = new FormData(form);

            fetch(form.action, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData,
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Failed to submit form for child ID ${childId}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        location.reload(); // Reload the page to reflect changes
                    } else {
                        console.error('Error saving changes:', data);
                        alert('Failed to save changes. Please try again.');
                    }
                })
                .catch(error => {
                    console.error('Error submitting form:', error);
                    alert('An error occurred while submitting the form.');
                });
        }
    });

    // Handle Delete Button Click
    childrenList.addEventListener('click', function (e) {
        if (e.target.classList.contains('delete-child-btn')) {
            const childId = e.target.dataset.childId;

            if (confirm('Are you sure you want to remove this child?')) {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

                fetch(`/delete-child/${childId}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken,
                    },
                })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`Failed to delete child ID ${childId}: ${response.statusText}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.success) {
                            document.getElementById(`child-${childId}`).remove();
                            alert('Child removed successfully.');
                        } else {
                            console.error('Error deleting child:', data);
                            alert('Failed to delete the child. Please try again.');
                        }
                    })
                    .catch(error => {
                        console.error('Error deleting child:', error);
                        alert('An error occurred while deleting the child.');
                    });
            }
        }
    });
});
