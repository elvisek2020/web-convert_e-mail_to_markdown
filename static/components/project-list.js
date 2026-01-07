/**
 * Komponenta pro zobrazení seznamu existujících projektů
 */
export class ProjectList {
  constructor(container, onProjectSelect) {
    this.container = container;
    this.onProjectSelect = onProjectSelect;
    this.projects = [];
  }

  async loadProjects() {
    try {
      const response = await fetch('/api/projects');
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
    if (!this.container) return;

    if (this.projects.length === 0) {
      this.container.innerHTML = `
        <div class="project-list-empty">
          <p>Zatím nejsou žádné projekty. Vytvořte první projekt zadáním názvu výše.</p>
        </div>
      `;
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
        <h3 class="project-list-title">Existující projekty:</h3>
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

