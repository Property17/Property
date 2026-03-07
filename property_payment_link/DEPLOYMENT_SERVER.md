# Deployment Checklist - property_payment_link (Server with SSL + Nginx)

When changes work locally but not on the server, follow these steps **after pushing code**:

## 1. Upgrade the Module (Required)
XML templates and Python code are loaded into the database. You **must** upgrade:

```bash
# Option A: Command line (replace 'odoo17' with your database name)
./odoo-bin -d odoo17 -u property_payment_link --stop-after-init

# Option B: Via Odoo UI
# Apps → property_payment_link → Upgrade
```

## 2. Restart Odoo
```bash
sudo systemctl restart odoo
# or
sudo service odoo restart
```

## 3. Clear Odoo Assets (if JS/CSS changes don't appear)
Assets (JS, CSS) are bundled and cached. To force regeneration:

**Option A - Via UI (Odoo 17):**
- Enable Developer Mode
- Settings → Technical → Database Structure → Clear Assets Bundles
- Or: Add `?debug=assets` to the URL, then reload (disables asset minification/caching)

**Option B - Via SQL:**
```sql
DELETE FROM ir_attachment WHERE url LIKE '/web/assets%';
```

**Option C - Restart with dev mode once:**
```bash
./odoo-bin -d odoo17 --dev=all
# Load the payment link page once, then restart normally
```

## 4. Nginx - Disable Caching for Odoo
Add to your nginx `location` block for Odoo:

```nginx
location / {
    proxy_pass http://127.0.0.1:8069;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Prevent caching of dynamic pages
    proxy_cache_bypass 1;
    proxy_no_cache 1;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

For static assets (`/web/assets/`), you can allow caching but with short TTL, or bypass:
```nginx
location /web/assets/ {
    proxy_pass http://127.0.0.1:8069;
    proxy_cache_valid 200 1m;  # Short cache, or use proxy_cache_bypass 1
}
```

## 5. Browser Cache
After deploying, test with:
- **Hard refresh:** Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Or open in **Incognito/Private** window

## 6. Verify Base URL (SSL)
In Odoo: **Settings → General Settings** → ensure **Base URL** uses `https://`:
- Correct: `https://yourdomain.com`
- Wrong: `http://yourdomain.com`

## 7. Check payment_link_nodb (if 404 when logged out)
If payment links return 404 for logged-out users, ensure:
- `payment_link_nodb` is in `server_wide_modules` in odoo.conf
- Payment links include `&db=yourdb` in the URL

---
**Version bumped to 0.2** – Upgrade the module to apply all template/asset changes.
