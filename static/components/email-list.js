/**
 * Komponenta pro zobrazení seznamu emailů v projektu
 */
export class EmailList {
  constructor(container) {
    this.container = container;
    this.emails = [];
  }

  async loadEmails(projectName) {
    if (!projectName) {
      this.render([]);
      return;
    }

    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectName)}/emails`);
      if (!response.ok) {
        if (response.status === 404) {
          // Projekt neexistuje nebo nemá emaily
          this.render([]);
          return;
        }
        throw new Error('Nepodařilo se načíst emaily');
      }
      const data = await response.json();
      this.emails = data.emails || [];
      this.render(this.emails);
    } catch (error) {
      console.error('Chyba při načítání emailů:', error);
      this.emails = [];
      this.render([]);
    }
  }

  render(emails) {
    if (!this.container) {
      console.error('EmailList: container is null');
      return;
    }

    // Skrýt boxík pokud není žádný email
    if (emails.length === 0) {
      this.container.innerHTML = '';
      this.container.style.display = 'none';
      return;
    }

    this.container.style.display = 'block';
    
    // Formátovat datum pro zobrazení
    const formatDate = (dateStr) => {
      if (!dateStr) return '';
      try {
        const date = new Date(dateStr);
        return date.toLocaleString('cs-CZ', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        });
      } catch {
        return dateStr;
      }
    };

    const emailsHtml = emails
      .map((email) => `
        <tr class="email-row">
          <td class="email-date">${this.escapeHtml(formatDate(email.date))}</td>
          <td class="email-from">${this.escapeHtml(email.from || '')}</td>
          <td class="email-subject">${this.escapeHtml(email.subject || '')}</td>
        </tr>
      `)
      .join('');

    this.container.innerHTML = `
      <div class="email-list box">
        <h3 class="email-list-title">Seznam emailů</h3>
        <div class="email-list-content">
          <table class="email-table">
            <thead>
              <tr>
                <th class="email-table-header">Datum</th>
                <th class="email-table-header">Odesílatel</th>
                <th class="email-table-header">Předmět</th>
              </tr>
            </thead>
            <tbody>
              ${emailsHtml}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  clear() {
    this.emails = [];
    this.render([]);
  }
}
