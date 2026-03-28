function toggleFileRemoval(hiddenInputId, button) {

  const hiddenInput = document.getElementById(hiddenInputId);

  if (hiddenInput.value === "1") {

      hiddenInput.value = "0";
      button.textContent = "Remove One Sheet";
      button.classList.remove("marked");

  } else {

      hiddenInput.value = "1";
      button.textContent = "Cancel Remove";
      button.classList.add("marked");

  }

}