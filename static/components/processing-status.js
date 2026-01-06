/**
 * ProcessingStatus komponenta pro zobrazení průběhu zpracování
 */
export class ProcessingStatus {
  constructor(container) {
    this.container = container;
    this.statusMessages = {
      converting: 'Konvertuji email do markdown...'
    };
  }

  render(status = 'converting') {
    const message = this.statusMessages[status] || 'Zpracovávám...';
    
    this.container.innerHTML = `
      <div class="processing-status box">
        <div class="processing-content">
          <div class="spinner"></div>
          <h2 class="processing-title">${message}</h2>
        </div>
      </div>
    `;
  }

  show() {
    this.container.style.display = 'block';
  }

  hide() {
    this.container.style.display = 'none';
  }
}

