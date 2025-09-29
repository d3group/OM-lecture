# marimo WebAssembly + GitHub Pages Template for Operations Management

This repository contains marimo notebooks used in a bachelor-level Operations Management lecture, with a focus on forecasting and inventory management. The notebooks are exported to WebAssembly and can be deployed to GitHub Pages for interactive teaching materials.

## 📚 Included Examples

- `apps/demand_management.py` - Forecasting lecture notebook.
- `apps/demand_management_live.py` - Lecture notebook of the live session.
- `apps/inventory_management.py` - Inventory management lecture notebook.


## 🚀 Usage

1. Fork this repository.
2. Add your marimo files to the `notebooks/` or `apps/` directory:
   1. `notebooks/` notebooks are exported with `--mode edit` (lecture / interactive notebooks).
   2. `apps/` notebooks are exported with `--mode run` (standalone web apps/demos).
3. Push to the `main` branch.
4. Go to repository **Settings > Pages** and change the "Source" dropdown to "GitHub Actions".
5. GitHub Actions will automatically build and deploy the site to GitHub Pages.

## Including data or assets

To include data or assets in your notebooks, add them to the `public/` directory.

For example, load an image from the `public/` directory in a notebook:

```markdown
<img src="public/logo.png" width="200" />
```

Load a CSV dataset from `public/` (example for a marimo notebook using polars):

```python
import polars as pl
df = pl.read_csv(mo.notebook_location() / "public" / "demand_history.csv")
```

## 🧪 Testing

To test the export process locally, run `scripts/build.py` from the root directory:

```bash
python scripts/build.py
```

This will export all notebooks into a folder called `_site/` in the repository root. To serve the exported site locally:

```bash
python -m http.server -d _site
```

Then open `http://localhost:8000` in your browser.

## ✅ Notes for Instructors

- Use `notebooks/` for interactive lecture material that students can edit.
- Use `apps/` for immutable demos or assignments where you want a fixed run environment.
- Include datasets and static assets in `public/` so they are bundled with the exported site.
