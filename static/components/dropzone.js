/**
 * Dropzone komponenta pro drag & drop upload
 */
export class Dropzone {
  constructor(container, onFileDrop) {
    this.container = container;
    this.onFileDrop = onFileDrop;
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
          <h2 class="dropzone-title">Přetáhněte .eml soubor sem</h2>
          <p class="dropzone-subtitle">nebo klikněte pro výběr souboru</p>
          <input
            type="file"
            accept=".eml"
            class="dropzone-input"
            id="file-input"
          />
          <label for="file-input" class="dropzone-button">
            Vybrat soubor
          </label>
        </div>
      </div>
    `;

    this.dropzone = this.container.querySelector('#dropzone');
    this.fileInput = this.container.querySelector('#file-input');
  }

  attachEvents() {
    // Drag & drop events
    this.dropzone.addEventListener('dragover', (e) => this.handleDragOver(e));
    this.dropzone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
    this.dropzone.addEventListener('drop', (e) => this.handleDrop(e));
    
    // File input change
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

    const files = Array.from(e.dataTransfer.files);
    const emlFile = files.find(f => f.name.endsWith('.eml'));

    if (emlFile) {
      this.onFileDrop(emlFile);
    } else {
      alert('Prosím nahrajte pouze .eml soubory');
    }
  }

  handleFileInput(e) {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.eml')) {
      this.onFileDrop(file);
    } else {
      alert('Prosím vyberte .eml soubor');
    }
    // Reset input
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

