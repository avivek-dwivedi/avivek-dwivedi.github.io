/* Minimal vanilla JS. Site remains usable if this is unavailable. */
(function () {
  "use strict";

  // ---- Mobile navigation ----
  var navToggle = document.querySelector(".nav-toggle");
  var navLinks = document.querySelector(".nav-links");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      var open = navLinks.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // ---- Mobile TOC toggle ----
  var tocToggle = document.querySelector(".toc-toggle");
  var toc = document.querySelector(".toc");
  if (tocToggle && toc) {
    tocToggle.addEventListener("click", function () {
      var collapsed = toc.classList.toggle("collapsed");
      tocToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
    });
    // default collapsed on mobile
    if (window.matchMedia("(max-width: 900px)").matches) {
      toc.classList.add("collapsed");
      tocToggle.setAttribute("aria-expanded", "false");
    }
  }

  // ---- Active TOC section via IntersectionObserver ----
  var tocAnchors = Array.prototype.slice.call(
    document.querySelectorAll(".toc a[data-toc]")
  );
  var headings = tocAnchors
    .map(function (a) {
      return document.getElementById(a.getAttribute("data-toc"));
    })
    .filter(Boolean);

  if (headings.length && "IntersectionObserver" in window) {
    var activeId = null;
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            activeId = entry.target.id;
            tocAnchors.forEach(function (a) {
              a.classList.toggle(
                "active",
                a.getAttribute("data-toc") === activeId
              );
            });
          }
        });
      },
      { rootMargin: "-80px 0px -70% 0px", threshold: 0 }
    );
    headings.forEach(function (h) { observer.observe(h); });
  }

  // ---- Copy code buttons ----
  var codeBlocks = document.querySelectorAll(".code-block");
  codeBlocks.forEach(function (block) {
    var pre = block.querySelector("pre");
    if (!pre) return;
    var btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.type = "button";
    btn.setAttribute("aria-label", "Copy code");
    btn.textContent = "Copy";
    btn.addEventListener("click", function () {
      var text = pre.textContent;
      var done = function () {
        btn.textContent = "Copied";
        btn.classList.add("copied");
        setTimeout(function () {
          btn.textContent = "Copy";
          btn.classList.remove("copied");
        }, 1400);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      } else {
        var ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); done(); } catch (e) {}
        document.body.removeChild(ta);
      }
    });
    block.appendChild(btn);
  });

  // ---- Footer year ----
  var yearEl = document.getElementById("year");
  if (yearEl) { yearEl.textContent = new Date().getFullYear(); }
})();