/**
 * ProcessingStatus komponenta pro zobrazení průběhu zpracování
 */
export class ProcessingStatus {
  constructor(container) {
    this.container = container;
  }

  render(status = 'converting', current = 0, total = 0) {
    const progressText = total > 1 ? ` (${current}/${total})` : '';
    const message = `Konvertuji email${total > 1 ? 'y' : ''} do markdown...${progressText}`;

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

