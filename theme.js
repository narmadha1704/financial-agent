document.body.classList.toggle("dark", localStorage.theme === "dark");
document.getElementById("theme").onclick = () => localStorage.theme = document.body.classList.toggle("dark") ? "dark" : "light";