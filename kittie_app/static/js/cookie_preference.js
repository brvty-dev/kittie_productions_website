document.addEventListener("DOMContentLoaded", function() {
  
    const switchInput = document.getElementById("cookie-switch");
    const formInput = document.querySelector("input[name='cookie_preference']");
  
    formInput.value = switchInput.checked ? "accept" : "reject";
  
    switchInput.addEventListener("change", function() {
      formInput.value = this.checked ? "accept" : "reject";
    });

});