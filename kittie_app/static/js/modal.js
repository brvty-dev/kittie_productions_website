document.addEventListener("DOMContentLoaded", function() {
    let modal = document.querySelectorAll('.modal');
    M.Modal.init(modal, {});

    let modalTriggerButtons = document.querySelectorAll('.modal-trigger');
    modalTriggerButtons.forEach(function(btn) {
      btn.addEventListener('click', function(event) {
        event.preventDefault();
        let target = btn.getAttribute('href');
        let modalInstance = M.Modal.getInstance(document.querySelector(target));
        modalInstance.open();
      });
    });
});