/**
 * ====================================================================
 * Academic Learning Platform - Core JavaScript (app.js)
 * Lightweight, Vanilla JS, Modular & Accessible
 * ====================================================================
 */

document.addEventListener('DOMContentLoaded', function () {
  'use strict';

  // --- 1. SIDEBAR TOGGLE & OFFCANVAS (MOBILE / TABLET) ---
  const sidebar = document.getElementById('appSidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarClose = document.getElementById('sidebarClose');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('show');
    if (sidebarOverlay) sidebarOverlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('show');
    if (sidebarOverlay) sidebarOverlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      if (sidebar && sidebar.classList.contains('show')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (sidebarClose) {
    sidebarClose.addEventListener('click', closeSidebar);
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  // Close sidebar on ESC key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeSidebar();
      closeAllDropdowns();
      closeAllModals();
    }
  });

  // --- 2. USER DROPDOWN TOGGLE ---
  const userDropdownBtn = document.getElementById('userDropdownBtn');
  const userDropdownMenu = document.getElementById('userDropdownMenu');

  function toggleDropdown(dropdownMenu, button) {
    const isExpanded = dropdownMenu.classList.contains('show');
    closeAllDropdowns();
    if (!isExpanded) {
      dropdownMenu.classList.add('show');
      if (button) button.setAttribute('aria-expanded', 'true');
    }
  }

  function closeAllDropdowns() {
    const menus = document.querySelectorAll('.dropdown-menu.show');
    menus.forEach(function (menu) {
      menu.classList.remove('show');
    });
    const buttons = document.querySelectorAll('[aria-expanded="true"]');
    buttons.forEach(function (btn) {
      btn.setAttribute('aria-expanded', 'false');
    });
  }

  if (userDropdownBtn && userDropdownMenu) {
    userDropdownBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      toggleDropdown(userDropdownMenu, userDropdownBtn);
    });
  }

  // Close dropdowns on outside click
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.user-dropdown')) {
      closeAllDropdowns();
    }
  });

  // --- 3. AUTO-DISMISS & CLOSE FOR ALERTS ---
  const alertCloseButtons = document.querySelectorAll('.alert-close');
  alertCloseButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const alert = this.closest('.alert');
      if (alert) {
        alert.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-6px)';
        setTimeout(function () {
          alert.remove();
        }, 200);
      }
    });
  });

  // --- 4. MODAL HELPERS ---
  window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('show');
      document.body.style.overflow = 'hidden';
    }
  };

  window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('show');
      document.body.style.overflow = '';
    }
  };

  function closeAllModals() {
    const modals = document.querySelectorAll('.modal-backdrop.show');
    modals.forEach(function (modal) {
      modal.classList.remove('show');
    });
    document.body.style.overflow = '';
  }

  // Close modal when clicking backdrop
  document.querySelectorAll('.modal-backdrop').forEach(function (modal) {
    modal.addEventListener('click', function (e) {
      if (e.target === modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
      }
    });
  });
});
