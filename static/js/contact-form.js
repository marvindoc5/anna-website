(function () {
  "use strict";

  var form = document.querySelector(".contact-form");
  if (!form) return;

  form.addEventListener("submit", function (e) {
    var agree = form.querySelector("#agree");
    var row = agree.closest(".checkbox-row");
    var errorEl = agree.closest(".form-group").querySelector(".field-error");

    if (!agree.checked) {
      e.preventDefault();
      if (errorEl) {
        errorEl.textContent = "Please confirm you agree to the Practice Principles before sending your message.";
        errorEl.classList.add("is-visible");
      }
      if (row) row.classList.add("has-error");
      agree.focus();
      agree.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (errorEl) {
      errorEl.classList.remove("is-visible");
      if (row) row.classList.remove("has-error");
    }
  });

  var agreeCheckbox = form.querySelector("#agree");
  if (agreeCheckbox) {
    agreeCheckbox.addEventListener("change", function () {
      var row = agreeCheckbox.closest(".checkbox-row");
      var errorEl = agreeCheckbox.closest(".form-group").querySelector(".field-error");
      if (agreeCheckbox.checked) {
        if (row) row.classList.remove("has-error");
        if (errorEl) errorEl.classList.remove("is-visible");
      }
    });
  }

  form.querySelectorAll("input, textarea").forEach(function (field) {
    field.addEventListener("input", function () {
      var group = field.closest(".form-group");
      if (!group) return;
      var errorEl = group.querySelector(".field-error");
      if (errorEl) errorEl.classList.remove("is-visible");
    });
  });
})();
