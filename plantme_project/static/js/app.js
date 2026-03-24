document.addEventListener('DOMContentLoaded', () => {
  const buttons = document.querySelectorAll('.btn');
  buttons.forEach((button) => {
    if (button.tagName === 'BUTTON') {
      button.addEventListener('click', () => {
        const original = button.textContent;
        button.textContent = 'Demo only';
        setTimeout(() => {
          button.textContent = original;
        }, 1200);
      });
    }
  });
});
