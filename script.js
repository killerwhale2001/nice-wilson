// ── Wait until the page is fully loaded before running any code ──
document.addEventListener("DOMContentLoaded", function () {

  // ── CTA button ──────────────────────────────────────────────────
  // querySelector finds the first element that matches the CSS selector
  const ctaButton = document.querySelector("#cta-button");

  ctaButton.addEventListener("click", function () {
    // Smoothly scroll to the "about" section when the button is clicked
    document.querySelector("#about").scrollIntoView({ behavior: "smooth" });
  });


  // ── Contact form ─────────────────────────────────────────────────
  const form = document.querySelector("#contact-form");
  const message = document.querySelector("#form-message");

  form.addEventListener("submit", function (event) {
    // Prevent the browser's default behavior of reloading the page
    event.preventDefault();

    // Read the values the user typed
    const name = document.querySelector("#name").value;
    const email = document.querySelector("#email").value;

    // Show a confirmation message
    message.textContent = "Thanks, " + name + "! We'll reach out to " + email + " soon.";

    // Clear the form fields
    form.reset();
  });

});
