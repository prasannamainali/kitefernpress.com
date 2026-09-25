// Kitefern Press: small progressive enhancements. The page works without JavaScript.
(function () {
  "use strict";

  // 1) Buy buttons with no real link yet become inert "Coming soon" labels.
  document.querySelectorAll("a.buy").forEach(function (a) {
    var href = (a.getAttribute("href") || "").trim();
    if (!/^https?:\/\//i.test(href)) {
      a.removeAttribute("href");
      a.setAttribute("aria-disabled", "true");
      a.setAttribute("role", "link");
    }
  });

  // 2) Book filters ("Who's it for?")
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip[data-filter]"));
  var books = Array.prototype.slice.call(document.querySelectorAll(".book[data-collection]"));
  var status = document.getElementById("filter-status");

  function applyFilter(name, fromUser) {
    var shown = 0;
    books.forEach(function (b) {
      var match = name === "all" || b.getAttribute("data-collection") === name;
      b.hidden = !match;
      if (match) shown++;
    });
    chips.forEach(function (c) {
      c.setAttribute("aria-pressed", String(c.getAttribute("data-filter") === name));
    });
    if (status && fromUser) {
      status.textContent = "Showing " + shown + (shown === 1 ? " book" : " books");
    }
  }

  chips.forEach(function (c) {
    c.addEventListener("click", function () { applyFilter(c.getAttribute("data-filter"), true); });
  });

  // Gift-guide cards jump to the book list with a filter applied.
  document.querySelectorAll("[data-jump-filter]").forEach(function (link) {
    link.addEventListener("click", function () {
      applyFilter(link.getAttribute("data-jump-filter"), true);
    });
  });

  // 3) Header border once the page scrolls.
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 8); };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // 4) Keep the copyright year current.
  var y = document.getElementById("year");
  if (y) y.textContent = String(new Date().getFullYear());
})();
