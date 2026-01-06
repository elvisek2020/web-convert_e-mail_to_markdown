/**
 * MessageBanner komponenta pro zobrazení zpráv (úspěch/chyba)
 */
export class MessageBanner {
  constructor(container) {
    this.container = container;
    this.hideTimeout = null;
  }

  showSuccess(message) {
    this.show(message, 'success');
  }

  showError(message) {
    this.show(message, 'error');
  }

  show(message, type = 'success') {
    // Zrušit předchozí timeout pokud existuje
    if (this.hideTimeout) {
      clearTimeout(this.hideTimeout);
    }

    // Nastavit třídu a obsah
    this.container.className = `message-banner ${type}`;
    this.container.innerHTML = `<p>${type === 'success' ? '✅' : '❌'} ${message}</p>`;
    this.container.style.display = 'block';

    // Skrýt po 5 sekundách
    this.hideTimeout = setTimeout(() => {
      this.hide();
    }, 5000);
  }

  hide() {
    this.container.style.display = 'none';
    if (this.hideTimeout) {
      clearTimeout(this.hideTimeout);
      this.hideTimeout = null;
    }
  }
}

