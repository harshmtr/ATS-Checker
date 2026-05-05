function selectTemplate(template) {
  localStorage.setItem("selectedTemplate", template);
  window.location.href = "editor.html";
}

function generateResume() {
  document.getElementById("preview-name").innerText =
    document.getElementById("name").value;

  document.getElementById("preview-role").innerText =
    document.getElementById("role").value;

  document.getElementById("preview-about").innerText =
    document.getElementById("about").value;
}