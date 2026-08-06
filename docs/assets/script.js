// JobVault Libre — small progressive-enhancement script.
// No frameworks, no tracking, no network calls.

document.addEventListener("DOMContentLoaded", () => {
  // Footer year
  document.querySelectorAll("[data-year]").forEach((el) => {
    el.textContent = new Date().getFullYear();
  });

  // Hide broken logo images gracefully (in case assets aren't added yet)
  // and reveal the text fallback mark instead. Purely cosmetic — page
  // content is never hidden behind JavaScript.
  document.querySelectorAll("img[data-logo]").forEach((img) => {
    img.addEventListener("error", () => {
      img.style.display = "none";
      const fallback = img.parentElement.querySelector(".brand-mark-fallback");
      if (fallback) fallback.style.display = "flex";
    });
  });
});
