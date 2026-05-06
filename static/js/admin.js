'use strict';

document.addEventListener('DOMContentLoaded', function () {
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl);
  });

  function normalizeText(value) {
    return (value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  var filterInputs = document.querySelectorAll('[data-section-filter-input]');
  filterInputs.forEach(function (input) {
    var targetSelector = input.getAttribute('data-filter-target');
    if (!targetSelector) {
      return;
    }

    var container = document.querySelector(targetSelector);
    if (!container) {
      return;
    }

    var sections = [].slice.call(container.querySelectorAll('[data-filter-section]'));
    var emptyState = container.querySelector('[data-section-empty-state]');

    function applyFilter() {
      var query = normalizeText(input.value);
      var visibleCount = 0;

      sections.forEach(function (section) {
        var declaredTitle = section.getAttribute('data-filter-title') || '';
        var fallbackTitleNode = section.querySelector('[data-section-title]');
        var fallbackTitle = fallbackTitleNode ? fallbackTitleNode.textContent : '';
        var title = normalizeText(declaredTitle || fallbackTitle);
        var isVisible = !query || title.indexOf(query) !== -1;

        section.classList.toggle('d-none', !isVisible);
        if (isVisible) {
          visibleCount += 1;
        }
      });

      if (emptyState) {
        emptyState.classList.toggle('d-none', visibleCount > 0);
      }
    }

    input.addEventListener('input', applyFilter);
    applyFilter();
  });
});
