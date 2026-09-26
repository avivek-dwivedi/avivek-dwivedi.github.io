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
  var indexEl = document.getElementById("article-index");
  if (planEl && "fetch" in window) {
    fetch("/data/writing-plan.json", { cache: "no-cache" })
      .then(function (r) {
        if (!r.ok) throw new Error("not ok");
        return r.json();
      })
      .then(function (plan) {
        if (indexEl) renderArticleIndex(indexEl, plan);
        else renderPlan(planEl, plan);
      })
      .catch(function () { /* keep static fallback */ });
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  // Series metadata with fallback
  function getSeriesMeta(plan) {
    return plan.series || {
      "production-ai-systems": { title: "Production AI Systems", description: "", order: 1 },
      "model-adaptation": { title: "Model Adaptation & Post-Training", description: "", order: 2 }
    };
  }

  // Group published articles by series, sorted by seriesOrder then article seriesOrder
  function groupBySeries(plan) {
    var pubs = plan.published || [];
    var seriesMeta = getSeriesMeta(plan);
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

    // Sort articles within each series by seriesOrder
    Object.keys(groups).forEach(function (s) {
      groups[s].sort(function (a, b) {
        return (a.seriesOrder || 99) - (b.seriesOrder || 99);
      });
    });

    // Sort series by their display order
    groupOrder.sort(function (a, b) {
      var oa = seriesMeta[a] ? seriesMeta[a].order : 99;
      var ob = seriesMeta[b] ? seriesMeta[b].order : 99;
      return oa - ob;
    });

    return { groups: groups, groupOrder: groupOrder, seriesMeta: seriesMeta };
  }

  // --- Homepage: compact series summary cards ---
  function renderPlan(container, plan) {
    container.innerHTML = "";
    var g = groupBySeries(plan);
    var seriesMeta = g.seriesMeta;

    var cardGrid = el("div", "series-card-grid");

    g.groupOrder.forEach(function (seriesKey) {
      var items = g.groups[seriesKey];
      if (items.length === 0) return;

      var meta = seriesMeta[seriesKey] || { title: seriesKey, description: "" };
      var card = el("div", "series-card");

      // Series title
      card.appendChild(el("p", "series-card-title", meta.title));

      // Description
      if (meta.description) {
        card.appendChild(el("p", "series-card-desc", meta.description));
      }

      // Published count with singular/plural
      var countText = items.length + (items.length === 1 ? " article" : " articles");
      card.appendChild(el("p", "series-card-count", countText));

      // Featured article preview (first in series order)
      var featured = items[0];
      var preview = el("div", "series-card-preview");
      preview.appendChild(el("p", "series-card-preview-label", "Start here"));
      var previewLink = el("a", "series-card-preview-title", featured.title);
      if (featured.url) previewLink.href = featured.url;
      preview.appendChild(previewLink);
      if (featured.focus) {
        preview.appendChild(el("p", "series-card-preview-focus", featured.focus));
      }
      card.appendChild(preview);

      // Explore series link
      var exploreLink = el("a", "series-card-explore", "Explore series →");
      exploreLink.href = "/articles/#" + seriesKey;
      card.appendChild(exploreLink);

      cardGrid.appendChild(card);
    });

    container.appendChild(cardGrid);

    // Current work — associated with its series
    if (plan.current) {
      var c = plan.current;
      var currentSeries = c.series || "production-ai-systems";
      var currentMeta = seriesMeta[currentSeries] || { title: currentSeries };
      container.appendChild(el("hr", "div"));

      var cblock = el("div", "notebook-block");
      cblock.appendChild(el("p", "notebook-label", "Currently working on"));
      cblock.appendChild(el("p", "notebook-series-ref", currentMeta.title));
      cblock.appendChild(el("h3", "notebook-title", c.title));

      var statusTag = el("span", "tag tag-status", "In progress");
      cblock.appendChild(statusTag);

      if (c.focus) {
        cblock.appendChild(el("p", "notebook-focus", c.focus));
      }
      if (c.workingOn) {
        cblock.appendChild(el("p", "notebook-working", c.workingOn));
      }
      container.appendChild(cblock);
    }
  }

  // --- Article index page: full reading lists ---
  function renderArticleIndex(container, plan) {
    container.innerHTML = "";
    var g = groupBySeries(plan);
    var seriesMeta = g.seriesMeta;

    // Jump links
    var jumpDiv = el("div", "index-jump-links");
    jumpDiv.appendChild(el("span", "index-jump-label", "Series:"));
    g.groupOrder.forEach(function (seriesKey) {
      var meta = seriesMeta[seriesKey] || { title: seriesKey };
      var link = el("a", "index-jump-link", meta.title);
      link.href = "#" + seriesKey;
      jumpDiv.appendChild(link);
    });
    container.appendChild(jumpDiv);

    // Series sections
    g.groupOrder.forEach(function (seriesKey) {
      var items = g.groups[seriesKey];
      var meta = seriesMeta[seriesKey] || { title: seriesKey, description: "" };

      var section = el("section", "index-series-section");
      section.id = seriesKey;

      section.appendChild(el("h2", "index-series-title", meta.title));
      if (meta.description) {
        section.appendChild(el("p", "index-series-desc", meta.description));
      }

      var countText = items.length + (items.length === 1 ? " article" : " articles") + " published";
      section.appendChild(el("p", "index-series-count", countText));

      // Article rows
      items.forEach(function (p, i) {
        var row = el("div", "index-article-row");

        var num = el("span", "index-article-num", String(p.seriesOrder || (i + 1)).padStart(2, "0"));
        row.appendChild(num);

        var body = el("div", "index-article-body");

        var titleLink = el("a", "index-article-title", p.title);
        if (p.url) titleLink.href = p.url;
        body.appendChild(titleLink);

        if (p.focus) {
          body.appendChild(el("p", "index-article-focus", p.focus));
        }

        row.appendChild(body);
        section.appendChild(row);
      });

      // Current work for this series
      if (plan.current && plan.current.series === seriesKey) {
        var c = plan.current;
        var currentRow = el("div", "index-article-row index-current-row");

        currentRow.appendChild(el("span", "index-article-num", "—"));

        var body = el("div", "index-article-body");
        body.appendChild(el("span", "index-current-title", c.title));
        body.appendChild(el("span", "tag tag-status", "In progress"));

        if (c.focus) {
          body.appendChild(el("p", "index-article-focus", c.focus));
        }
        if (c.workingOn) {
          body.appendChild(el("p", "index-current-working", c.workingOn));
        }

        currentRow.appendChild(body);
        section.appendChild(currentRow);
      }

      container.appendChild(section);
    });
  }
})();