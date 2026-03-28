document.addEventListener("DOMContentLoaded", function() {

  let flashMessages = document.querySelectorAll(".flash");
  let closeButtons = document.querySelectorAll(".close-alert");

  function fadeOut(element) {
    element.classList.add("fade-out");

    setTimeout(function() {
      element.style.display = "none";
    }, 1000); // match CSS duration
  }

  flashMessages.forEach(function(flashMessage) {
    setTimeout(function() {
      fadeOut(flashMessage);
    }, 5000);
  });

  closeButtons.forEach(function(closeButton) {
    closeButton.addEventListener("click", function() {
      let flashMessage = this.closest(".flash");
      if (flashMessage) {
        fadeOut(flashMessage);
      }
    });
  });

});