document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("predictionForm");
    if (form) {
      form.addEventListener("submit", function (e) {
        const submitButton = form.querySelector("button[type='submit']");
        submitButton.disabled = true;
        submitButton.innerText = "Predicting...";
      });
    }
  });
  