document.addEventListener('DOMContentLoaded', function () {
    console.log("✅ upgrade_required.js loaded");
  
    const form = document.getElementById('upgrade-form');
  
    if (!form) {
      console.warn("⛔ upgrade-form not found");
      return;
    }
  
    const selectedPlanInput = document.getElementById('selected-plan');
    const planRadios = document.querySelectorAll('input[name="plan"]');
    const boxes = document.querySelectorAll('.simple-box');
  
    planRadios.forEach(radio => {
      radio.addEventListener('change', () => {
        selectedPlanInput.value = radio.value;
        console.log(`📦 Plan selected: ${radio.value}`);
        boxes.forEach(box => box.classList.remove('selected'));
        radio.closest('.simple-box').classList.add('selected');
      });
    });
  
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
      console.log("🟢 Upgrade form submitted");
  
      const formData = new FormData(form);
      console.log("📤 Sending selected plan:", formData.get("selected_plan"));
  
      try {
        const response = await fetch(form.action || "/start-checkout/", {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: formData
        });
  
        const data = await response.json();
        console.log("📥 Server response:", data);
  
        if (response.ok && data.id) {
          console.log("✅ Stripe session ID received:", data.id);
          const stripe = Stripe(STRIPE_PUBLIC_KEY);
          stripe.redirectToCheckout({ sessionId: data.id });
        } else {
          console.error("❌ Backend returned error:", data.form_errors || data);
          alert(data.error || "An unexpected error occurred.");
        }
      } catch (error) {
        console.error("🚨 Upgrade request failed:", error);
        alert("Something went wrong. Please try again.");
      }
    });
  });
  