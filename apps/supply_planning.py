import marimo

__generated_with = "0.15.5"
app = marimo.App(
    width="medium",
    app_title="Supply Planning and Purchasing",
    layout_file="layouts/supply_planning.slides.json",
    css_file="d3.css",
)

@app.cell(hide_code=True)
def _():
    GH_USER = "d3group"
    GH_REPO = "OM-lecture"
    BRANCH = "purchasing"

    def raw_url(*parts: str) -> str:
        path = "/".join(parts)
        return f"https://raw.githubusercontent.com/{GH_USER}/{GH_REPO}/{BRANCH}/{path}"

    class DataURLs:
        BASE = raw_url("apps", "public", "data")
        DEMAND = f"{BASE}/daily_demand_data_fuerth.csv"
        FORECAST = f"{BASE}/forecast_fuerth.csv"
        HISTORIC_FORECAST = f"{BASE}/historic_forecast_fuerth.csv"
        

    class ImageURLs:
        BASE = raw_url("apps", "public", "images")
        DISTRIBUTION_CENTER = f"{BASE}/distribution_center_fuerth.png"

    class UtilsURLs:
        BASE = raw_url("apps", "utils")
        FILES = {
            "data.py": f"{BASE}/data.py",
            "forecast.py": f"{BASE}/forecast.py",
            "slides.py": f"{BASE}/slides.py",
            "inventory.py": f"{BASE}/inventory.py",
        }
        PACKAGES = [
            "pandas",
            "altair",
            "scikit-learn",
            "numpy",
            "statsmodels",
            "scipy",
            "typing_extensions",
            "utilsforecast"
        ]

    return (DataURLs, ImageURLs, UtilsURLs)



@app.cell(hide_code=True)
async def _(UtilsURLs):
    import micropip
    import urllib.request
    import os

    class UtilsManager:
        def __init__(self, dest_folder="utils", files_map=None, packages=None):
            self.dest_folder = dest_folder
            self.files_map = files_map or {}
            self.files = list(self.files_map.keys())
            self.packages = packages or []
            self.packages_installed = False
            self.files_downloaded = False

        async def install_packages(self):
            for pkg in self.packages:
                try: 
                    __import__(pkg)
                    print(f"✅ Package {pkg} is already installed.")
                    continue
                except ImportError:
                    print(f"Installing {pkg}...")
                    await micropip.install(pkg)
            print("✅ All packages installed.")
            self.packages_installed = True

        def download_files(self):
            os.makedirs(self.dest_folder, exist_ok=True)
            init_file = os.path.join(self.dest_folder, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w") as f:
                    f.write("# Init for utils package\n")

            for fname, url in self.files_map.items():
                dest_path = os.path.join(self.dest_folder, fname)
                urllib.request.urlretrieve(url, dest_path)
                print(f"📥 Downloaded {fname} to {dest_path}")

            self.files_downloaded = True

    utils_manager = UtilsManager(
        files_map=UtilsURLs.FILES,
        packages=UtilsURLs.PACKAGES,
    )

    await utils_manager.install_packages()
    utils_manager.download_files()

    return (utils_manager,)