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
    const dropzoneContainer = document.getElementById('dropzone-container');
    this.dropzone = new Dropzone(dropzoneContainer, (files) => this.handleFilesDrop(files));

    // Processing Status
    const processingOverlay = document.getElementById('processing-overlay');
    this.processingStatus = new ProcessingStatus(processingOverlay);

    // Message Banner
    const messageBanner = document.getElementById('message-banner');
    this.messageBanner = new MessageBanner(messageBanner);

    // Project List
    const projectListContainer = document.getElementById('project-list-container');
    this.projectList = new ProjectList(
      projectListContainer,
      (projectName) => {
        this.handleProjectSelect(projectName);
      },
      () => {
        // Reset email listu při změně filtru
        if (this.emailList) {
          this.emailList.clear();
        }
        // Vymazat také input pole
        const projectInput = document.getElementById('project-name');
        if (projectInput) {
          projectInput.value = '';
          this.state.projectName = '';
        }
      }
    );

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

  async handleFilesDrop(files) {
    if (!this.state.projectName || !this.state.projectName.trim()) {
      alert('Prosím zadejte název projektu');
      return;
    }

    const emlFiles = files.filter(f => f.name.endsWith('.eml'));
    if (emlFiles.length === 0) {
      alert('Prosím nahrajte pouze .eml soubory');
      return;
    }

    this.setState({ status: 'converting' });
    this.messageBanner.hide();

    const total = emlFiles.length;
    let success = 0;
    let skipped = 0;
    const errors = [];

    for (let i = 0; i < total; i++) {
      this.processingStatus.render('converting', i + 1, total);
      try {
        await this.sendFileViaREST(emlFiles[i]);
        success++;
      } catch (error) {
        if (error.statusCode === 409) {
          skipped++;
        } else {
          errors.push(`${emlFiles[i].name}: ${error.message}`);
        }
      }
    }

    this.setState({ status: 'idle' });

    if (this.projectList) {
      await this.projectList.loadProjects();
    }
    if (this.emailList && this.state.projectName) {
      await this.emailList.loadEmails(this.state.projectName);
    }

    if (total === 1 && success === 1) {
      this.messageBanner.showSuccess('Email byl úspěšně uložen');
    } else if (errors.length === 0) {
      const parts = [`${success} uloženo`];
      if (skipped > 0) parts.push(`${skipped} přeskočeno (duplikát)`);
      this.messageBanner.showSuccess(`Hotovo: ${parts.join(', ')}`);
    } else {
      const parts = [`${success} uloženo`];
      if (skipped > 0) parts.push(`${skipped} přeskočeno`);
      parts.push(`${errors.length} chyb`);
      this.messageBanner.showError(`${parts.join(', ')}. ${errors[0]}`);
    }
  }

  async sendFileViaREST(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_name', this.state.projectName.trim());

    const response = await fetch('/api/convert-email', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const err = new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      err.statusCode = response.status;
      throw err;
    }

    return await response.json();
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

