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

  // ---- Engineering Notebook: render writing-plan.json ----
  var planEl = document.getElementById("writing-plan");
  if (planEl && "fetch" in window) {
    fetch("/data/writing-plan.json", { cache: "no-cache" })
      .then(function (r) {
        if (!r.ok) throw new Error("not ok");
        return r.json();
      })
      .then(function (plan) { renderPlan(planEl, plan); })
      .catch(function () { /* keep static fallback */ });
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function renderPlan(container, plan) {
    container.innerHTML = "";

    // Published — group by series
    var pubs = plan.published || [];
    if (pubs.length) {
      // Series metadata
      var seriesMeta = {
        "production-ai-systems": "Production AI Systems",
        "model-adaptation": "Model Adaptation & Post-Training"
      };

      // Group articles by series (backward-compatible: no series = production-ai-systems)
      var groups = {};
      var groupOrder = [];
      pubs.forEach(function (p) {
        var s = p.series || "production-ai-systems";
        if (!groups[s]) {
          groups[s] = [];
          groupOrder.push(s);
        }
        groups[s].push(p);
      });

      groupOrder.forEach(function (seriesKey) {
        var items = groups[seriesKey];
        var seriesLabel = seriesMeta[seriesKey] || seriesKey;

        var seriesBlock = el("div", "notebook-block");
        seriesBlock.appendChild(el("p", "notebook-series-label", seriesLabel));
        seriesBlock.appendChild(el("p", "notebook-label", "Published / " + String(items.length).padStart(2, "0")));

        items.forEach(function (p, i) {
          var item = el("div", "notebook-pub-item");
          var num = el("span", "notebook-num", String(i + 1).padStart(2, "0"));
          item.appendChild(num);
          item.appendChild(el("h3", "notebook-title", p.title));
          if (p.focus) item.appendChild(el("p", "notebook-focus", p.focus));
          if (p.url) {
            var a = el("a", "notebook-link", "Read →");
            a.href = p.url;
            item.appendChild(a);
          }
          seriesBlock.appendChild(item);
          if (i < items.length - 1) {
            seriesBlock.appendChild(el("hr", "div"));
          }
        });
        container.appendChild(seriesBlock);

        // Add divider between series groups (not after the last one if current follows)
        if (groupOrder.indexOf(seriesKey) < groupOrder.length - 1) {
          container.appendChild(el("hr", "div"));
        }
      });
    }

    // Current
    if (plan.current) {
      var c = plan.current;
      container.appendChild(el("hr", "div"));
      var cblock = el("div", "notebook-block");
      cblock.appendChild(el("p", "notebook-label", "Now"));
      cblock.appendChild(el("h3", "notebook-title", c.title));
      if (c.focus) {
        var fcLine = el("p", "notebook-focus", c.focus);
        cblock.appendChild(fcLine);
      }
      if (c.workingOn) {
        var woLine = el("p", "notebook-working", c.workingOn);
        cblock.appendChild(woLine);
      }
      container.appendChild(cblock);
    }
  }
})();