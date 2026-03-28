const corporateMenus = document.querySelectorAll('.corporate_menu');

corporateMenus.forEach((menu) => {
  const trigger = menu.querySelector('.corporate_link');

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();

    document.querySelectorAll('.corporate_menu.open').forEach((openMenu) => {
      if (openMenu !== menu) {
        openMenu.classList.remove('open');
      }
    });

    menu.classList.toggle('open');
  });
});

document.addEventListener('click', () => {
  document.querySelectorAll('.corporate_menu.open').forEach((menu) => {
    menu.classList.remove('open');
  });
});