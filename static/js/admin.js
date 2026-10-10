function filterByOffice(selectEl) {
    const officeId = selectEl.value;
    const target = document.querySelector(selectEl.dataset.target);
    if (!target) return;

    Array.from(target.options).forEach(function (option) {
        if (!option.value) {
            option.hidden = false;
            return;
        }
        const match = !officeId || option.dataset.office === officeId;
        option.hidden = !match;
        if (!match && option.selected) {
            target.value = "";
        }
    });

    if (target.classList.contains("js-dept-filter") || target.dataset.target) {
        filterByDept(target);
    }
}

function filterByDept(selectEl) {
    const deptId = selectEl.value;
    const target = document.querySelector(selectEl.dataset.target);
    if (!target) return;

    Array.from(target.options).forEach(function (option) {
        if (!option.value) {
            option.hidden = false;
            return;
        }
        const match = !deptId || option.dataset.dept === deptId;
        option.hidden = !match;
        if (!match && option.selected) {
            target.value = "";
        }
    });
}

document.addEventListener("change", function (event) {
    if (event.target.classList.contains("js-office-filter")) {
        filterByOffice(event.target);
    }
    if (event.target.classList.contains("js-dept-filter")) {
        filterByDept(event.target);
    }
});

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".js-office-filter").forEach(function (el) {
        if (el.value) filterByOffice(el);
    });
});
