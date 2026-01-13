import { Dropzone } from './components/dropzone.js';
import { ProcessingStatus } from './components/processing-status.js';
import { MessageBanner } from './components/message-banner.js';
import { ProjectList } from './components/project-list.js';
import { EmailList } from './components/email-list.js';
import { ThemeToggle } from './components/theme-toggle.js';

/**
 * Hlavní aplikace
 */
class App {
  constructor() {
    this.state = {
      status: 'idle', // 'idle' | 'converting' | 'success' | 'error'
      projectName: '',
      version: null
    };

    this.dropzone = null;
    this.processingStatus = null;
    this.messageBanner = null;
    this.projectList = null;
    this.emailList = null;
    this.themeToggle = null;

    this.init();
  }

  async init() {
    // Načíst verzi
    await this.loadVersion();

    // Inicializovat komponenty
    this.initComponents();

    // Nastavit event listenery
    this.setupEventListeners();

    // Načíst seznam projektů
    if (this.projectList) {
      await this.projectList.loadProjects();
    }
  }

  async loadVersion() {
    try {
      const response = await fetch('/version.json');
      const data = await response.json();
      if (data.version) {
        this.state.version = `v.${data.version}`;
        const versionEl = document.getElementById('version');
        if (versionEl) {
          versionEl.textContent = this.state.version;
        }
      }
    } catch (error) {
      console.error('Chyba při načítání verze:', error);
    }
  }

  initComponents() {
    // Dropzone
    const dropzoneContainer = document.getElementById('dropzone-container');
    this.dropzone = new Dropzone(dropzoneContainer, (file) => this.handleFileDrop(file));

    // Processing Status
    const processingOverlay = document.getElementById('processing-overlay');
    this.processingStatus = new ProcessingStatus(processingOverlay);

    // Message Banner
    const messageBanner = document.getElementById('message-banner');
    this.messageBanner = new MessageBanner(messageBanner);

    // Project List
    const projectListContainer = document.getElementById('project-list-container');
    this.projectList = new ProjectList(projectListContainer, (projectName) => {
      this.handleProjectSelect(projectName);
    });

    // Email List
    const emailListContainer = document.getElementById('email-list-container');
    this.emailList = new EmailList(emailListContainer);

    // Theme Toggle
    const themeToggleContainer = document.getElementById('theme-toggle-container');
    this.themeToggle = new ThemeToggle(themeToggleContainer);
  }

  setupEventListeners() {
    // Project name input
    const projectInput = document.getElementById('project-name');
    projectInput.addEventListener('input', (e) => {
      this.state.projectName = e.target.value;
    });
  }

  async handleProjectSelect(projectName) {
    // Vyplnit input pole názvem projektu
    const projectInput = document.getElementById('project-name');
    if (projectInput) {
      projectInput.value = projectName;
      this.state.projectName = projectName;
      
      // Focus na input pro lepší UX
      projectInput.focus();
    }

    // Načíst a zobrazit seznam emailů pro vybraný projekt
    if (this.emailList) {
      await this.emailList.loadEmails(projectName);
    }
  }

  async handleFileDrop(file) {
    if (!file.name.endsWith('.eml')) {
      alert('Prosím nahrajte pouze .eml soubory');
      return;
    }

    if (!this.state.projectName || !this.state.projectName.trim()) {
      alert('Prosím zadejte název projektu');
      return;
    }

    try {
      this.setState({ status: 'converting' });
      this.messageBanner.hide();

      // Použít REST API pro všechny soubory
      await this.sendFileViaREST(file);
    } catch (error) {
      console.error('Chyba při zpracování:', error);
      this.setState({ status: 'idle' });
      const errorMsg = error.message || 'Nastala chyba při zpracování emailu';
      this.messageBanner.showError(errorMsg);
    }
  }

  async sendFileViaREST(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_name', this.state.projectName.trim());

    const response = await fetch('/api/convert-email', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    this.setState({ status: 'idle' });
    const message = `Email byl úspěšně uložen: ${result.filename}`;
    this.messageBanner.showSuccess(message);
    
    // Aktualizovat seznam projektů po úspěšném uložení
    if (this.projectList) {
      await this.projectList.loadProjects();
    }
    
    // Aktualizovat seznam emailů, pokud je projekt vybrán
    if (this.emailList && this.state.projectName) {
      await this.emailList.loadEmails(this.state.projectName);
    }
  }

  setState(newState) {
    this.state = { ...this.state, ...newState };
    this.updateUI();
  }

  updateUI() {
    const projectInput = document.getElementById('project-name');
    const dropzoneContainer = document.getElementById('dropzone-container');
    const processingOverlay = document.getElementById('processing-overlay');

    // Aktualizovat stav inputu
    if (projectInput) {
      projectInput.disabled = this.state.status === 'converting';
    }

    // Zobrazit/skrýt processing overlay
    if (this.state.status === 'converting') {
      this.processingStatus.render('converting');
      this.processingStatus.show();
      if (this.dropzone) {
        this.dropzone.setEnabled(false);
      }
    } else {
      this.processingStatus.hide();
      if (this.dropzone) {
        this.dropzone.setEnabled(true);
      }
    }
  }
}

// Inicializovat aplikaci po načtení DOM
document.addEventListener('DOMContentLoaded', () => {
  new App();
});

