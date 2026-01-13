/**
 * Komponenta pro přepínání tmavého/světlého režimu
 */
export class ThemeToggle {
  constructor(container) {
    this.container = container;
    this.currentTheme = this.getStoredTheme() || 'light';
    
    // Nastavit počáteční téma okamžitě (před renderováním)
    this.applyTheme(this.currentTheme);
    
    // Vytvořit UI
    this.init();
  }

  init() {
    // Vytvořit UI
    this.render();
  }

  getStoredTheme() {
    try {
      return localStorage.getItem('theme') || 'light';
    } catch {
      return 'light';
    }
  }

  setStoredTheme(theme) {
    try {
      localStorage.setItem('theme', theme);
    } catch {
      // Ignorovat chyby localStorage
    }
  }

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    this.currentTheme = theme;
    this.setStoredTheme(theme);
  }

  toggle() {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.applyTheme(newTheme);
    this.updateButton();
  }

  updateButton() {
    const icon = this.container.querySelector('.theme-icon');
    const text = this.container.querySelector('.theme-toggle-text');
    
    if (icon && text) {
      if (this.currentTheme === 'dark') {
        icon.textContent = '☀️';
        text.textContent = 'Světlý režim';
      } else {
        icon.textContent = '🌙';
        text.textContent = 'Tmavý režim';
      }
    }
  }

  render() {
    if (!this.container) {
      console.error('ThemeToggle: container is null');
      return;
    }

    const icon = this.currentTheme === 'dark' ? '☀️' : '🌙';
    const text = this.currentTheme === 'dark' ? 'Světlý režim' : 'Tmavý režim';
    
    this.container.innerHTML = `
      <button class="theme-toggle-button" type="button" aria-label="Přepnout režim">
        <span class="theme-icon">${icon}</span>
        <span class="theme-toggle-text">${text}</span>
      </button>
    `;
    
    // Přidat event listener
    const toggleButton = this.container.querySelector('.theme-toggle-button');
    if (toggleButton) {
      // Odstranit případné existující listenery
      const newButton = toggleButton.cloneNode(true);
      toggleButton.parentNode.replaceChild(newButton, toggleButton);
      
      // Přidat nový listener
      newButton.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggle();
      });
    }
  }
}
