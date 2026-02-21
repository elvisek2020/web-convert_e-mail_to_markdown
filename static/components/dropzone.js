/**
 * Dropzone komponenta pro drag & drop upload (single + multi-file)
 */
export class Dropzone {
  constructor(container, onFilesDrop) {
    this.container = container;
    this.onFilesDrop = onFilesDrop;
    this.isDragging = false;
    this.init();
  }

  init() {
    this.render();
    this.attachEvents();
  }

  render() {
    this.container.innerHTML = `
      <div class="dropzone" id="dropzone">
        <div class="dropzone-content">
          <div class="dropzone-icon">📧</div>
          <h2 class="dropzone-title">Přetáhněte .eml soubory sem</h2>
          <p class="dropzone-subtitle">nebo klikněte pro výběr souborů (i více najednou)</p>
          <input
            type="file"
            accept=".eml"
            multiple
            class="dropzone-input"
            id="file-input"
          />
          <label for="file-input" class="dropzone-button">
            Vybrat soubory
          </label>
        </div>
      </div>
    `;

    this.dropzone = this.container.querySelector('#dropzone');
    this.fileInput = this.container.querySelector('#file-input');
  }

  attachEvents() {
    this.dropzone.addEventListener('dragover', (e) => this.handleDragOver(e));
    this.dropzone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
    this.dropzone.addEventListener('drop', (e) => this.handleDrop(e));
    this.fileInput.addEventListener('change', (e) => this.handleFileInput(e));
  }

  handleDragOver(e) {
    e.preventDefault();
    this.isDragging = true;
    this.dropzone.classList.add('dragging');
  }

  handleDragLeave(e) {
    e.preventDefault();
    this.isDragging = false;
    this.dropzone.classList.remove('dragging');
  }

  handleDrop(e) {
    e.preventDefault();
    this.isDragging = false;
    this.dropzone.classList.remove('dragging');

    const emlFiles = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.eml'));

    if (emlFiles.length > 0) {
      this.onFilesDrop(emlFiles);
    } else {
      alert('Prosím nahrajte pouze .eml soubory');
    }
  }

  handleFileInput(e) {
    const emlFiles = Array.from(e.target.files).filter(f => f.name.endsWith('.eml'));
    if (emlFiles.length > 0) {
      this.onFilesDrop(emlFiles);
    } else {
      alert('Prosím vyberte .eml soubory');
    }
    e.target.value = '';
  }

  setEnabled(enabled) {
    if (enabled) {
      this.dropzone.style.pointerEvents = 'auto';
      this.dropzone.style.opacity = '1';
    } else {
      this.dropzone.style.pointerEvents = 'none';
      this.dropzone.style.opacity = '0.5';
    }
  }
}

