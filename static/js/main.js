document.addEventListener('DOMContentLoaded', () => {
  const burger = document.querySelector('.burger');
  const nav = document.querySelector('.main-nav');
  if (burger && nav) {
    burger.addEventListener('click', () => {
      const opened = nav.classList.toggle('is-open');
      burger.setAttribute('aria-expanded', String(opened));
    });
  }

  const search = document.getElementById('service-search');
  const results = document.getElementById('service-results');
  const loading = document.getElementById('search-loading');
  const empty = document.getElementById('no-services');
  let timer;
  if (search && results) {
    search.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        loading.hidden = false;
        try {
          const response = await fetch(`/api/services/?q=${encodeURIComponent(search.value)}`);
          if (!response.ok) throw new Error('Ошибка запроса');
          const data = await response.json();
          results.replaceChildren();
          data.results.forEach(item => {
            const card = document.createElement('article');
            card.className = 'service-card';
            const icon = document.createElement('div');
            icon.className = 'service-icon';
            icon.textContent = '✧';
            const title = document.createElement('h2');
            title.textContent = item.name;
            const description = document.createElement('p');
            description.textContent = item.description || 'Бережная обработка ваших вещей.';
            const price = document.createElement('strong');
            price.textContent = `от ${Number(item.price).toLocaleString('ru-RU')} ₽`;
            card.append(icon, title, description, price);
            results.append(card);
          });
          empty.hidden = data.results.length !== 0;
        } catch (error) {
          empty.hidden = false;
          empty.textContent = 'Не удалось загрузить результаты. Обновите страницу.';
        } finally {
          loading.hidden = true;
        }
      }, 250);
    });
  }

  ['order-form', 'register-form'].forEach(id => {
    const form = document.getElementById(id);
    if (!form) return;
    form.addEventListener('submit', event => {
      const required = [...form.querySelectorAll('input[required], select[required], textarea[required]')];
      const invalid = required.find(field => !field.value.trim());
      const email = form.querySelector('input[type="email"]');
      const password = form.querySelector('input[type="password"]');
      const error = document.getElementById('client-error');
      if (invalid || (email && email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) || (password && password.value.length < 8)) {
        event.preventDefault();
        error.textContent = invalid ? 'Заполните обязательные поля.' : (email && email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value) ? 'Проверьте формат электронной почты.' : 'Пароль должен содержать не менее 8 символов.');
        if (invalid) invalid.focus();
      } else if (error) {
        error.textContent = '';
      }
    });
  });
});
