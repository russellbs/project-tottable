document.addEventListener("DOMContentLoaded", function () {
    const radios = document.querySelectorAll('input[name="plan"]');
    const hiddenInput = document.querySelector('form input[name="selected_plan"]');
    const pricingBoxes = document.querySelectorAll('.simple-box');

    // Set initial hidden input value based on checked radio
    const checkedRadio = document.querySelector('input[name="plan"]:checked');
    if (checkedRadio && hiddenInput) {
        hiddenInput.value = checkedRadio.value;
        console.log("Initial plan on page load:", checkedRadio.value);
    }

    // Handle radio change events
    radios.forEach(radio => {
        radio.addEventListener('change', function () {
            if (hiddenInput) {
                hiddenInput.value = this.value;
                console.log("Plan selected:", this.value);
            }

            // Update visual styling
            pricingBoxes.forEach(box => box.classList.remove('selected'));
            const selectedBox = this.closest('.simple-box');
            if (selectedBox) {
                selectedBox.classList.add('selected');
            }
        });
    });

    // Handle OAuth button clicks to store plan in session before redirect
    const oauthButtons = document.querySelectorAll('.oauth-button');
    oauthButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();

            const selectedPlan = hiddenInput ? hiddenInput.value : 'monthly';
            const redirectUrl = this.href;

            fetch("/set-plan/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                },
                body: JSON.stringify({ selected_plan: selectedPlan })
            }).then(() => {
                window.location.href = redirectUrl;
            }).catch(err => {
                console.error("Error setting plan in session:", err);
                window.location.href = redirectUrl;  // Fallback
            });
        });
    });
});
