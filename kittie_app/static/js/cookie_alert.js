document.addEventListener('DOMContentLoaded', function() {
    var cookieAlerts = document.querySelectorAll('.cookie-alert');
    cookieAlerts.forEach(function(alert, index) {
        setTimeout(function() {
            alert.classList.add('show');
        }, index * 1000);
    });

    var closeButtons = document.querySelectorAll('.cookie-alert .hide_alert');
    closeButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            event.preventDefault();

            var alertBox = button.closest('.cookie-alert');
            if (alertBox) {
                alertBox.style.display = 'none';
            }

            document.cookie = "message_viewed_closed=true; max-age=31536000; path=/";
        });
    });
});