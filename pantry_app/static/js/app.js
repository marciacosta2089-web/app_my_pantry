(function() {
  const barcodeInputs = document.querySelectorAll('input[name="barcode"]');
  barcodeInputs.forEach(input => {
    input.addEventListener('change', () => {
      const value = input.value.trim();
      if (value) {
        const note = document.createElement('div');
        note.className = 'small text-muted';
        note.innerText = 'Barcode stored locally so future scans autofill name and category.';
        input.parentElement.appendChild(note);
        fetch(`/barcode/${value}`)
          .then(resp => resp.json())
          .then(data => {
            if (data.found) {
              const nameField = input.closest('form').querySelector('input[name="name"]');
              if (nameField && !nameField.value) nameField.value = data.name;
              if (data.category_name) {
                const select = input.closest('form').querySelector('select[name="category_id"]');
                if (select) {
                  const option = Array.from(select.options).find(o => o.text === data.category_name);
                  if (option) option.selected = true;
                }
              }
            }
          });
      }
    });
  });
})();
