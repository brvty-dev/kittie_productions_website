document.addEventListener('DOMContentLoaded', function () {
  var elems = document.querySelectorAll('select');
  var instances = M.FormSelect.init(elems);

  var select = document.getElementById('mySelect');
  if (select) {
    var instance = M.FormSelect.getInstance(select);

    select.addEventListener('change', function () {
      var selectedValues = instance.getSelectedValues();
      console.log(selectedValues);
    });
  }
});