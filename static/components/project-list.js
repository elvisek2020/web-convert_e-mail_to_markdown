/**
 * Komponenta pro zobrazení seznamu existujících projektů
 */
export class ProjectList {
  constructor(container, onProjectSelect, onFilterChange) {
    this.container = container;
    this.onProjectSelect = onProjectSelect;
    this.onFilterChange = onFilterChange;
    this.projects = [];
    this.includeOthers = false;
  }

  async loadProjects() {
    try {
      const url = `/api/projects?include_others=${this.includeOthers}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Nepodařilo se načíst projekty');
      }
      const data = await response.json();
      this.projects = data.projects || [];
      this.render();
    } catch (error) {
      console.error('Chyba při načítání projektů:', error);
      this.projects = [];
      this.render();
    }
  }

  render() {
    if (!this.container) {
      console.error('ProjectList: container is null');
      return;
    }

    // Vytvořit header s checkboxem
    const headerHtml = `
      <div class="project-list-header">
        <h3 class="project-list-title">Seznam projektů</h3>
        <label class="project-list-checkbox-label">
          <input 
            type="checkbox" 
            class="project-list-checkbox" 
            ${this.includeOthers ? 'checked' : ''}
          />
          <span>Zobrazit ostatní</span>
        </label>
      </div>
    `;

    if (this.projects.length === 0) {
      this.container.innerHTML = `
        <div class="project-list-content">
          ${headerHtml}
          <div class="project-list-empty">
            <p>Zatím nejsou žádné projekty. Vytvořte první projekt zadáním názvu výše.</p>
          </div>
        </div>
      `;
      
      // Přidat event listener na checkbox i když není žádný projekt
      const checkbox = this.container.querySelector('.project-list-checkbox');
      if (checkbox) {
        checkbox.addEventListener('change', (e) => {
          this.includeOthers = e.target.checked;
          this.loadProjects();
        });
      }
      return;
    }

    const projectsHtml = this.projects
      .map(
        (project) => `
        <div class="project-item" data-project="${this.escapeHtml(project)}">
          ${this.escapeHtml(project)}
        </div>
      `
      )
      .join('');

    this.container.innerHTML = `
      <div class="project-list-content">
        ${headerHtml}
        <div class="project-list-items">
          ${projectsHtml}
        </div>
      </div>
    `;

    // Přidat event listenery na kliknutí
    const projectItems = this.container.querySelectorAll('.project-item');
    projectItems.forEach((item) => {
      item.addEventListener('click', () => {
        const projectName = item.getAttribute('data-project');
        if (this.onProjectSelect) {
          this.onProjectSelect(projectName);
        }
      });
    });

    // Přidat event listener na checkbox
    const checkbox = this.container.querySelector('.project-list-checkbox');
    if (checkbox) {
      checkbox.addEventListener('change', (e) => {
        this.includeOthers = e.target.checked;
        // Zavolat callback pro změnu filtru (pro reset email listu)
        if (this.onFilterChange) {
          this.onFilterChange();
        }
        this.loadProjects();
      });
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  refresh() {
    this.loadProjects();
  }
}

