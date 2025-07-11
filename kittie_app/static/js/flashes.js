document.addEventListener("DOMContentLoaded", function() {
  let closeButtons = document.querySelectorAll(".close-alert");
  
  closeButtons.forEach(function(closeButton) {
      closeButton.addEventListener("click", function() {
          let flashMessage = this.closest(".flash");
          if (flashMessage) {
          flashMessage.style.display = "none";
          }
      });
  });
});