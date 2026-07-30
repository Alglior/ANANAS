/**
 * A.N.A.N.A.S — Upload : tag selector with search, categories, toggle chips
 */
UploadModule.tagSelector = (function () {
  var tagsInput = document.getElementById('tags');
  var searchInput = document.getElementById('tagSearch');
  var categories = document.getElementById('tagCategories');
  var noResults = document.getElementById('tagNoResults');
  var selectedTags = new Set();

  function getCurrentTags() {
    var val = tagsInput ? tagsInput.value.trim() : '';
    return val ? val.split(',').map(function (t) { return t.trim(); }).filter(function (t) { return t; }) : [];
  }

  function syncInput() {
    if (!tagsInput) return;
    tagsInput.value = Array.from(selectedTags).join(', ');
  }

  function toggleTag(tag) {
    if (selectedTags.has(tag)) {
      selectedTags['delete'](tag);
    } else {
      selectedTags.add(tag);
    }
    syncInput();
    refreshChips();
  }

  function refreshChips() {
    document.querySelectorAll('.tag-chip').forEach(function (chip) {
      var tag = chip.getAttribute('data-tag');
      if (selectedTags.has(tag)) {
        chip.classList.add('active');
      } else {
        chip.classList.remove('active');
      }
    });
  }

  function filterTags(query) {
    var lower = query.toLowerCase().trim();
    var anyVisible = false;

    document.querySelectorAll('.tag-category').forEach(function (cat) {
      var body = cat.querySelector('.tag-category-body');
      var chips = cat.querySelectorAll('.tag-chip');
      var catMatch = false;

      chips.forEach(function (chip) {
        var tag = chip.getAttribute('data-tag');
        if (!lower || tag.toLowerCase().includes(lower)) {
          chip.style.display = '';
          catMatch = true;
        } else {
          chip.style.display = 'none';
        }
      });

      if (catMatch) {
        cat.style.display = '';
        anyVisible = true;
        var toggle = cat.querySelector('.tag-category-toggle');
        if (lower) {
          toggle.setAttribute('aria-expanded', 'true');
          body.hidden = false;
        }
      } else {
        cat.style.display = 'none';
      }
    });

    if (noResults) noResults.hidden = anyVisible;
  }

  function init() {
    if (!tagsInput || !categories) return;

    // Restore selected tags from input value on edit
    getCurrentTags().forEach(function (t) { selectedTags.add(t); });

    // Chip click
    categories.addEventListener('click', function (e) {
      var chip = e.target.closest('.tag-chip');
      if (chip) {
        e.preventDefault();
        toggleTag(chip.getAttribute('data-tag'));
      }
    });

    // Category toggle
    categories.addEventListener('click', function (e) {
      var toggle = e.target.closest('.tag-category-toggle');
      if (toggle) {
        e.preventDefault();
        var body = toggle.parentNode.querySelector('.tag-category-body');
        var expanded = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', !expanded);
        body.hidden = expanded;
        toggle.querySelector('.tag-category-arrow').textContent = expanded ? '\u25B6' : '\u25BC';
      }
    });

    // Search
    if (searchInput) {
      searchInput.addEventListener('input', function () {
        filterTags(this.value);
      });
    }

    refreshChips();
  }

  return { init: init, toggleTag: toggleTag, getCurrentTags: function () { return Array.from(selectedTags); } };
})();