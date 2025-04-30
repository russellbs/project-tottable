document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('signup-form');

    if (!form) return;

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";").map(c => c.trim());
            for (let cookie of cookies) {
                if (cookie.startsWith(name + "=")) {
                    cookieValue = decodeURIComponent(cookie.split("=")[1]);
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrfToken = getCookie("csrftoken");

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const formData = new FormData(form);

        try {
            const response = await fetch(form.action || "/signup/", {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok && data.id) {
                const stripe = Stripe(STRIPE_PUBLIC_KEY);
                stripe.redirectToCheckout({ sessionId: data.id });
            } else {
                alert(data.error || "An unexpected error occurred.");
                console.error(data.form_errors || data);
            }
        } catch (error) {
            console.error("Signup error", error);
            alert("Something went wrong. Please try again.");
        }
    });
});
