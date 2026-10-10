/**
 * QueueLess Government Digital Service - Frontend Interactive Engine
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss Flash Alert Messages after 4 seconds
    const flashAlerts = document.querySelectorAll('.alert-dismissible');
    flashAlerts.forEach(function (alert) {
        setTimeout(function () {
            if (alert) {
                alert.classList.remove('show');
                alert.classList.add('fade');
                setTimeout(function () {
                    alert.remove();
                }, 300);
            }
        }, 4000);
    });

    // 2. Real-time Client-side Search/Filter for Data Tables
    const searchInputs = document.querySelectorAll('.table-search-input, [data-table-search]');
    searchInputs.forEach(function (input) {
        const targetSelector = input.getAttribute('data-table-search') || 'table';
        const targetTable = document.querySelector(targetSelector);
        
        if (!targetTable) return;

        input.addEventListener('input', function () {
            const query = this.value.toLowerCase().trim();
            const rows = targetTable.querySelectorAll('tbody tr');

            rows.forEach(function (row) {
                // If it's an empty-state row (e.g. "No records found"), skip
                if (row.querySelector('td[colspan]')) return;

                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });

    // 3. Dynamic Toast Notification Pop-up Helper
    window.showQueueToast = function (title, message, type = 'primary') {
        let toastContainer = document.getElementById('queueToastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'queueToastContainer';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '1100';
            document.body.appendChild(toastContainer);
        }

        const toastId = 'toast-' + Date.now();
        const toastEl = document.createElement('div');
        toastEl.id = toastId;
        toastEl.className = `toast align-items-center text-bg-${type} border-0 shadow-lg`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');

        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong class="d-block mb-1">${title}</strong>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        toastContainer.appendChild(toastEl);
        const bsToast = new bootstrap.Toast(toastEl, { delay: 6000 });
        bsToast.show();

        toastEl.addEventListener('hidden.bs.toast', function () {
            toastEl.remove();
        });
    };

    // 4. Modal Confirmation for Sensitive Actions (Cancel / Skip)
    let confirmModalEl = document.getElementById('globalConfirmModal');
    if (!confirmModalEl) {
        const modalHtml = `
            <div class="modal fade" id="globalConfirmModal" tabindex="-1" aria-labelledby="confirmModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow">
                        <div class="modal-header border-0 pb-0">
                            <h5 class="modal-title fw-bold" id="confirmModalLabel">
                                <i class="bi bi-exclamation-triangle-fill text-warning me-2"></i> Confirm Action
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body py-3 text-secondary" id="confirmModalBody">
                            Are you sure you want to proceed with this action?
                        </div>
                        <div class="modal-footer border-0 pt-0">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-danger fw-semibold" id="confirmModalProceedBtn">Proceed</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        confirmModalEl = document.getElementById('globalConfirmModal');
    }

    const confirmModal = new bootstrap.Modal(confirmModalEl);
    const confirmBody = document.getElementById('confirmModalBody');
    const confirmProceedBtn = document.getElementById('confirmModalProceedBtn');
    let pendingFormOrAction = null;

    document.addEventListener('click', function (e) {
        const trigger = e.target.closest('[data-confirm], .confirm-action');
        if (trigger) {
            e.preventDefault();
            const message = trigger.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
            confirmBody.textContent = message;

            if (trigger.tagName === 'A') {
                pendingFormOrAction = () => { window.location.href = trigger.href; };
            } else if (trigger.tagName === 'BUTTON' && trigger.form) {
                pendingFormOrAction = () => { trigger.form.submit(); };
            } else {
                pendingFormOrAction = () => { trigger.click(); };
            }

            confirmModal.show();
        }
    });

    confirmProceedBtn.addEventListener('click', function () {
        confirmModal.hide();
        if (typeof pendingFormOrAction === 'function') {
            pendingFormOrAction();
            pendingFormOrAction = null;
        }
    });
});
