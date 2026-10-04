# kitefernpress.com

The website for Kitefern Press. It's plain HTML and CSS with no build step, no framework and no tracking.

```
index.html          the whole site (one page)
404.html            "page not found" page
CNAME               tells GitHub Pages to serve the site at kitefernpress.com
.nojekyll           tells GitHub Pages to serve files exactly as they are
robots.txt, sitemap.xml
assets/css/style.css
assets/js/main.js   book filters + "Coming soon" buttons (the site still works without it)
assets/fonts/       Fraunces + Source Sans 3, self-hosted (SIL Open Font License)
assets/img/covers/  the 10 front covers (640 px WebP)
assets/img/prints/  the 15 Etsy printable wall art thumbnails (720 x 540 px WebP)
assets/img/         favicon, app icon, logo, social-share image
```

---

## 1. Add an Amazon link when a book goes live

1. Open `index.html` and search for the book's id (list below).
2. A few lines under it, find `<a class="buy" href=""`.
3. Paste the link between the quotes:
   `<a class="buy" href="https://amzn.to/3AbCdEf" target="_blank" rel="sponsored noopener">`
4. Save, commit and push. The button switches from **Coming soon to Amazon** to **Buy on Amazon** on its own.

| Book | id to search for |
|---|---|
| Remember When (live) | `remember-when` |
| Porch Light Christmas Word Search (live) | `porch-light-christmas` |
| Porch Light Word Search, Volume 2 | `porch-light-word-search-2` |
| Porch Light Sudoku (live) | `porch-light-sudoku` |
| Grandma's Kitchen Table Stories | `grandmas-kitchen-table-stories` |
| Grandpa's Front Porch Stories | `grandpas-front-porch-stories` |
| Mom's Kitchen Table Stories | `moms-kitchen-table-stories` |
| Dad's Front Porch Stories | `dads-front-porch-stories` |
| Maze Quest (live; the renamed Kite Trail Mazes) | `maze-quest` |
| Kite Trail Christmas | `kite-trail-christmas` |
| Kite Trail Mazes Jr. | `kite-trail-mazes-jr` |
| Caregiver Daily Log Book | `caregiver-daily-log-book` |

Each book also has its own shareable link, for example `https://kitefernpress.com/#maze-quest`.

Affiliate notes:
- Get the link from Amazon Associates (the SiteStripe bar on the product page), or use the format `https://www.amazon.com/dp/ASIN?tag=YOURTAG-20`.
- Add `kitefernpress.com` to the website list in your Associates account.
- Keep the disclosure in the footer. It's already there.
- The site doesn't show prices on purpose. Amazon's Associates rules don't allow prices that are copied by hand and can go out of date.
- Don't buy your own books through your own affiliate link.

---

## 2. Put the site on GitHub Pages

1. On GitHub, create a new **public** repository, for example `kitefernpress.com`. Don't add a README; this folder already has one.
2. In Terminal:

   ```bash
   cd ~/Downloads/"Kitefern Press KDP"/Website
   git init
   git add .
   git commit -m "Launch kitefernpress.com"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/kitefernpress.com.git
   git push -u origin main
   ```

3. In the repo, go to **Settings → Pages**:
   - **Source:** Deploy from a branch
   - **Branch:** `main`, folder `/ (root)`. Click **Save**.
   - **Custom domain:** `kitefernpress.com` (the `CNAME` file fills this in). Click **Save**.
4. Recommended: verify the domain so nobody else can claim it on GitHub. Go to your GitHub profile's **Settings → Pages → Add a domain**, enter `kitefernpress.com`, and add the TXT record it gives you in Cloudflare.

---

## 3. Point the domain at GitHub with Cloudflare

If you bought the domain somewhere other than Cloudflare, first add it to Cloudflare and change the nameservers at your registrar to the two Cloudflare gives you.

Then go to **Cloudflare → kitefernpress.com → DNS → Records**. Delete any parking records for `@` or `www`, and add these:

| Type | Name | Content | Proxy status |
|---|---|---|---|
| A | `@` | `185.199.108.153` | DNS only (grey cloud) |
| A | `@` | `185.199.109.153` | DNS only |
| A | `@` | `185.199.110.153` | DNS only |
| A | `@` | `185.199.111.153` | DNS only |
| AAAA | `@` | `2606:50c0:8000::153` | DNS only |
| AAAA | `@` | `2606:50c0:8001::153` | DNS only |
| AAAA | `@` | `2606:50c0:8002::153` | DNS only |
| AAAA | `@` | `2606:50c0:8003::153` | DNS only |
| CNAME | `www` | `YOUR-USERNAME.github.io` | DNS only |

(The IPs come from GitHub's docs: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)

Next:
1. Go back to **GitHub → Settings → Pages**. Wait until the DNS check passes. This usually takes minutes, but it can take up to 24 hours.
2. Tick **Enforce HTTPS** as soon as it's available. GitHub issues the certificate for free.
3. Visit `https://kitefernpress.com` and `https://www.kitefernpress.com`. Both should load the site.

**Should I turn on the orange cloud (Cloudflare proxy)?** It's optional. Leaving it on **DNS only** is the most reliable setup, because GitHub handles HTTPS and renews its own certificate. If you want Cloudflare's caching or its free Web Analytics:
- Turn the proxy on only **after** HTTPS works on GitHub.
- Set **SSL/TLS → Overview → Full (strict)**. Never use "Flexible", which causes an endless redirect loop.
- GitHub's Pages settings may then show a DNS warning, and its certificate renewals can sometimes fail. If the site ever shows a certificate error, switch the records back to DNS only.

---

## 4. Set up hello@kitefernpress.com (free, forwards to Gmail)

1. **Cloudflare → kitefernpress.com → Email → Email Routing → Get started.**
2. Create the custom address `hello` and set the destination to your Gmail address.
3. Open the verification email Cloudflare sends to Gmail and confirm it.
4. When Cloudflare offers to add the MX and TXT (SPF) records, click **Add records and enable**. These records don't affect the website.
5. Test it by sending an email to hello@kitefernpress.com from another account.

Email Routing only *receives* mail. To reply *as* hello@kitefernpress.com from Gmail, you need an outgoing mail (SMTP) service added under Gmail's "Send mail as". That's optional. Replying from your Gmail address works fine.

---

## Printable wall art (Etsy)

The "Wall art" section (`id="prints"` in `index.html`) shows the Etsy prints from the kitefernpress shop
(https://www.etsy.com/shop/kitefernpress). Each card links to its listing as `https://www.etsy.com/listing/LISTING-ID`.

| Print | Listing ID |
|---|---|
| He Counts the Stars (Psalm 147:4) | 4584646077 |
| The Heavens Declare (Psalm 19:1) | 4584654726 |
| When I Consider Thy Heavens (Psalm 8:3) | 4584655148 |
| New Every Morning (Lamentations 3:22-23) | 4584647365 |
| Established Forever as the Moon (Psalm 89:37) | 4584656004 |
| He Made the Stars Also (Genesis 1:16) | 4584739128 |
| Look Now Toward Heaven (Genesis 15:5) | 4584732203 |
| Shine as Lights in the World (Philippians 2:15) | 4584732507 |
| The Nutcracker, Christmas Eve | 4584637541 |
| Nutcracker Trio (Merry Christmas) | 4584641135 |
| Waltz of the Snowflakes | 4584649924 |
| Nutcracker Ornaments | 4584650330 |
| Moon Scripture Set of 4 | 4584739970 |
| Sun, Moon & Stars Set of 4 | 4584733127 |
| Nutcracker Christmas Set of 4 | 4584653582 |

To add a print: save a 720 x 540 px `.webp` of the listing's first photo in `assets/img/prints/`, copy one
`<li class="print">…</li>` block in `index.html`, change the link, image and text, then commit and push.
If you deactivate a listing (for example the Nutcracker prints after Christmas), remove or comment out its card
so the link doesn't lead to an unavailable page.

---

## Preview on your Mac

```bash
cd ~/Downloads/"Kitefern Press KDP"/Website
python3 -m http.server 8000
```
Then open http://localhost:8000.

## Adding a new book later

1. Save a 640 px wide cover as `.webp` in `assets/img/covers/`.
2. In `index.html`, copy an existing `<article class="book">…</article>` block, then change the `id`, the image and the text.
3. Set `data-collection` to one of `puzzles`, `journals`, `kids` or `care`.
4. Update the numbers on the filter buttons (the `<span class="count">` values).
5. Update `<lastmod>` in `sitemap.xml`, then commit and push.
