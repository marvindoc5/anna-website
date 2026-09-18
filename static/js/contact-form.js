(function () {
  "use strict";

  var form = document.querySelector(".contact-form");
  if (!form) return;

  var EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function showError(el, message) {
    if (!el) return;
    if (message) el.textContent = message;
    el.classList.add("is-visible");
  }

  function hideError(el) {
    if (el) el.classList.remove("is-visible");
  }

  function fieldErrorFor(el) {
    var group = el.closest(".form-group");
    return group ? group.querySelector(".field-error") : null;
  }

  var nameInput = form.querySelector("#name");
  var emailInput = form.querySelector("#email");
  var agreeCheckbox = form.querySelector("#agree");
  var interestGroup = form.querySelector('.choice-group input[name="interest"]')
    ? form.querySelector('input[name="interest"]').closest(".choice-group")
    : null;
  var counsellingGroup = form.querySelector('input[name="counselling_type"]')
    ? form.querySelector('input[name="counselling_type"]').closest(".choice-group")
    : null;

  form.addEventListener("submit", function (e) {
    var firstInvalid = null;

    // Name
    if (!nameInput.value.trim()) {
      nameInput.classList.add("has-error");
      showError(fieldErrorFor(nameInput), "Please enter your name.");
      firstInvalid = firstInvalid || nameInput;
    } else {
      nameInput.classList.remove("has-error");
      hideError(fieldErrorFor(nameInput));
    }

    // Email
    if (!emailInput.value.trim() || !EMAIL_PATTERN.test(emailInput.value.trim())) {
      emailInput.classList.add("has-error");
      showError(
        fieldErrorFor(emailInput),
        emailInput.value.trim() ? "Please enter a valid email address." : "Please enter your email address."
      );
      firstInvalid = firstInvalid || emailInput;
    } else {
      emailInput.classList.remove("has-error");
      hideError(fieldErrorFor(emailInput));
    }

    // Interested in
    if (interestGroup) {
      var interestChecked = form.querySelector('input[name="interest"]:checked');
      if (!interestChecked) {
        interestGroup.classList.add("has-error");
        showError(fieldErrorFor(interestGroup), "Please let me know what you're interested in.");
        firstInvalid = firstInvalid || interestGroup;
      } else {
        interestGroup.classList.remove("has-error");
        hideError(fieldErrorFor(interestGroup));
      }
    }

    // Type of counselling
    if (counsellingGroup) {
      var counsellingChecked = form.querySelector('input[name="counselling_type"]:checked');
      if (!counsellingChecked) {
        counsellingGroup.classList.add("has-error");
        showError(fieldErrorFor(counsellingGroup), "Please select a type of counselling.");
        firstInvalid = firstInvalid || counsellingGroup;
      } else {
        counsellingGroup.classList.remove("has-error");
        hideError(fieldErrorFor(counsellingGroup));
      }
    }

    // Agreement checkbox
    var agreeRow = agreeCheckbox.closest(".checkbox-row");
    if (!agreeCheckbox.checked) {
      if (agreeRow) agreeRow.classList.add("has-error");
      showError(fieldErrorFor(agreeCheckbox), "Please confirm you agree to the Practice Principles before sending your message.");
      firstInvalid = firstInvalid || agreeCheckbox;
    } else {
      if (agreeRow) agreeRow.classList.remove("has-error");
      hideError(fieldErrorFor(agreeCheckbox));
    }

    if (firstInvalid) {
      e.preventDefault();
      firstInvalid.focus();
      firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });

  // Clear error state as soon as the visitor starts fixing a field.
  [nameInput, emailInput].forEach(function (field) {
    field.addEventListener("input", function () {
      field.classList.remove("has-error");
      hideError(fieldErrorFor(field));
    });
  });

  [interestGroup, counsellingGroup].forEach(function (group) {
    if (!group) return;
    group.querySelectorAll("input").forEach(function (radio) {
      radio.addEventListener("change", function () {
        group.classList.remove("has-error");
        hideError(fieldErrorFor(group));
      });
    });
  });

  agreeCheckbox.addEventListener("change", function () {
    if (agreeCheckbox.checked) {
      var row = agreeCheckbox.closest(".checkbox-row");
      if (row) row.classList.remove("has-error");
      hideError(fieldErrorFor(agreeCheckbox));
    }
  });
})();
