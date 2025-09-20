// Кастомный JavaScript для Django Admin Panel с темой Unfold

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎛️ Django Admin Panel с темой Unfold загружен');
    
    // Инициализация компонентов
    initDashboard();
    initTables();
    initFilters();
    initTooltips();
    initAnimations();
});

// Dashboard функции
function initDashboard() {
    const dashboardCards = document.querySelectorAll('.dashboard-card');
    
    dashboardCards.forEach((card, index) => {
        // Анимация появления карточек
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
        
        // Эффект hover
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
            this.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
        });
    });
}

// Функции для таблиц
function initTables() {
    const tables = document.querySelectorAll('.admin-table');
    
    tables.forEach(table => {
        // Добавляем класс для стилизации
        table.classList.add('admin-table');
        
        // Добавляем эффект hover для строк
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f9fafb';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
        
        // Добавляем сортировку по клику на заголовки
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            if (header.textContent.trim() !== '') {
                header.style.cursor = 'pointer';
                header.addEventListener('click', function() {
                    sortTable(table, Array.from(headers).indexOf(this));
                });
            }
        });
    });
}

// Функция сортировки таблицы
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const isAscending = table.getAttribute('data-sort-direction') !== 'asc';
    
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();
        
        // Попытка сравнения как числа
        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // Сравнение как строки
        return isAscending ? 
            aText.localeCompare(bText) : 
            bText.localeCompare(aText);
    });
    
    // Перестраиваем таблицу
    rows.forEach(row => tbody.appendChild(row));
    
    // Обновляем направление сортировки
    table.setAttribute('data-sort-direction', isAscending ? 'asc' : 'desc');
    
    // Обновляем визуальные индикаторы
    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        header.classList.remove('sort-asc', 'sort-desc');
        if (index === columnIndex) {
            header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        }
    });
}

// Функции для фильтров
function initFilters() {
    const filterSections = document.querySelectorAll('.filter-section');
    
    filterSections.forEach(section => {
        const inputs = section.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                // Добавляем класс для анимации
                this.classList.add('filter-changed');
                
                // Убираем класс через короткое время
                setTimeout(() => {
                    this.classList.remove('filter-changed');
                }, 300);
            });
        });
    });
    
    // Добавляем функциональность быстрого поиска
    const searchInputs = document.querySelectorAll('input[type="search"], input[name="q"]');
    searchInputs.forEach(input => {
        input.classList.add('search-box');
        
        // Добавляем индикатор загрузки при поиске
        input.addEventListener('input', debounce(function() {
            showSearchLoading(this);
        }, 300));
    });
}

// Функция показа загрузки поиска
function showSearchLoading(input) {
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-spinner';
    loadingIndicator.style.position = 'absolute';
    loadingIndicator.style.right = '10px';
    loadingIndicator.style.top = '50%';
    loadingIndicator.style.transform = 'translateY(-50%)';
    
    const inputContainer = input.parentElement;
    inputContainer.style.position = 'relative';
    
    // Убираем предыдущий индикатор
    const existingIndicator = inputContainer.querySelector('.loading-spinner');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    inputContainer.appendChild(loadingIndicator);
    
    // Убираем индикатор через 1 секунду
    setTimeout(() => {
        loadingIndicator.remove();
    }, 1000);
}

// Функции для tooltip
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip-text';
        tooltip.textContent = element.getAttribute('data-tooltip');
        
        element.classList.add('tooltip');
        element.appendChild(tooltip);
    });
}

// Функции анимации
function initAnimations() {
    // Анимация появления элементов при скролле
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);
    
    // Наблюдаем за элементами, которые должны анимироваться
    const animatedElements = document.querySelectorAll('.admin-table, .filter-section, .dashboard-card');
    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

// Утилитарные функции
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Функция для показа уведомлений
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification-${type}`;
    notification.textContent = message;
    
    // Добавляем в начало страницы
    const content = document.querySelector('.unfold-content') || document.body;
    content.insertBefore(notification, content.firstChild);
    
    // Убираем через 5 секунд
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Функция для обновления статистики в реальном времени
function updateDashboardStats() {
    // Здесь можно добавить AJAX запросы для обновления статистики
    console.log('Обновление статистики dashboard...');
}

// Функция для экспорта данных
function exportData(format = 'csv') {
    const table = document.querySelector('.admin-table');
    if (!table) return;
    
    const rows = Array.from(table.querySelectorAll('tr'));
    let csvContent = '';
    
    rows.forEach(row => {
        const cells = Array.from(row.querySelectorAll('th, td'));
        const rowData = cells.map(cell => `"${cell.textContent.trim()}"`).join(',');
        csvContent += rowData + '\n';
    });
    
    // Создаем и скачиваем файл
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Функция для быстрого поиска по всем таблицам
function quickSearch(query) {
    const tables = document.querySelectorAll('.admin-table');
    
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const matches = text.includes(query.toLowerCase());
            
            row.style.display = matches ? '' : 'none';
        });
    });
}

// Добавляем глобальные функции для использования в консоли
window.HRAdmin = {
    showNotification,
    updateDashboardStats,
    exportData,
    quickSearch,
    sortTable
};

// Обработка ошибок
window.addEventListener('error', function(e) {
    console.error('Ошибка в Django Admin Panel:', e.error);
    showNotification('Произошла ошибка. Проверьте консоль браузера.', 'error');
});

// Обработка успешных AJAX запросов
document.addEventListener('ajaxSuccess', function(e) {
    showNotification('Операция выполнена успешно', 'success');
});

// Обработка ошибок AJAX
document.addEventListener('ajaxError', function(e) {
    showNotification('Ошибка при выполнении операции', 'error');
});

console.log('✅ Django Admin Panel JavaScript загружен успешно');
