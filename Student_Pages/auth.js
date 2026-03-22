(function () {
  var tabs = document.querySelectorAll(".auth-tab");
  var panelLogin = document.getElementById("panel-login");
  var panelSignup = document.getElementById("panel-signup");
  var formLogin = document.getElementById("form-login");
  var formSignup = document.getElementById("form-signup");
  var dropZone = document.getElementById("student-id-drop");
  var fileInput = document.getElementById("student-id-file");
  var fileNameEl = document.getElementById("student-id-filename");
  var signupMsg = document.getElementById("signup-msg");
  var panelsRoot = document.getElementById("auth-panels");

  function showPanel(mode) {
    var isLogin = mode === "login";
    tabs.forEach(function (t) {
      var active = t.getAttribute("data-mode") === mode;
      t.classList.toggle("is-active", active);
      t.setAttribute("aria-selected", active ? "true" : "false");
    });
    if (panelsRoot) {
      panelsRoot.classList.toggle("auth-panels--login", isLogin);
      panelsRoot.classList.toggle("auth-panels--signup", !isLogin);
    }
    if (panelLogin) {
      panelLogin.setAttribute("aria-hidden", isLogin ? "false" : "true");
    }
    if (panelSignup) {
      panelSignup.setAttribute("aria-hidden", isLogin ? "true" : "false");
    }
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      var mode = tab.getAttribute("data-mode");
      if (mode) showPanel(mode);
    });
  });

  function setFileName(name) {
    if (!fileNameEl) return;
    fileNameEl.textContent = name ? "Selected: " + name : "";
  }

  if (dropZone && fileInput) {
    dropZone.addEventListener("click", function () {
      fileInput.click();
    });

    dropZone.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        fileInput.click();
      }
    });

    ["dragenter", "dragover"].forEach(function (ev) {
      dropZone.addEventListener(ev, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add("is-dragover");
      });
    });

    ["dragleave", "drop"].forEach(function (ev) {
      dropZone.addEventListener(ev, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("is-dragover");
      });
    });

    dropZone.addEventListener("drop", function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length) {
        fileInput.files = files;
        setFileName(files[0].name);
      }
    });

    fileInput.addEventListener("change", function () {
      var f = fileInput.files && fileInput.files[0];
      setFileName(f ? f.name : "");
    });
  }

  if (formLogin) {
    formLogin.addEventListener("submit", function (e) {
      e.preventDefault();
      /* Wire to your backend when ready */
    });
  }

  if (formSignup) {
    formSignup.addEventListener("submit", function (e) {
      e.preventDefault();
      if (signupMsg) {
        signupMsg.classList.remove("is-error", "is-ok");
        signupMsg.textContent = "";
      }

      var p1 = document.getElementById("signup-password");
      var p2 = document.getElementById("signup-password-confirm");
      if (p1 && p2 && p1.value !== p2.value) {
        if (signupMsg) {
          signupMsg.textContent = "Passwords do not match.";
          signupMsg.classList.add("is-error");
        }
        return;
      }

      if (fileInput && (!fileInput.files || !fileInput.files.length)) {
        if (signupMsg) {
          signupMsg.textContent = "Please upload a photo or scan of your student ID.";
          signupMsg.classList.add("is-error");
        }
        return;
      }

      /* Wire to your backend when ready */
      if (signupMsg) {
        signupMsg.textContent = "Form is valid — connect this page to your server to create an account.";
        signupMsg.classList.add("is-ok");
      }
    });
  }
})();
