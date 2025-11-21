import marimo

__generated_with = "0.13.4"
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
        BASE = raw_url("apps", "public", "data", "supply_planning")
        QR_PARAMS = f"{BASE}/qr_policy_parameters.csv"
        SUPPLY_PLAN = f"{BASE}/supply_plan_simulation.csv"



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

    return DataURLs, UtilsURLs


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


@app.cell(hide_code=True)
def _():
    import warnings
    warnings.filterwarnings("ignore")
    return


@app.cell(hide_code=True)
def _(utils_manager):
    print("Packages installed:", utils_manager.packages_installed)
    print("Files downloaded:", utils_manager.files_downloaded)
    from utils.slides import SlideCreator
    from utils.data import DataLoader
    from utils.inventory import SimpleForecastPlotter, SafetyStockPlotter
    from sklearn.utils import Bunch
    import marimo as mo
    return SlideCreator, mo


@app.cell(hide_code=True)
def _(mo):
    public_dir = (
        str(mo.notebook_location) + "/public"
        if str(mo.notebook_location).startswith("https://")
        else "public"
    )
    return


@app.cell
def _():
    lehrstuhl = "Chair of Logistics and Quantitative Methods"
    vorlesung = "Operations Management"
    presenter = "Richard Pibernik, Moritz Beck"
    return lehrstuhl, presenter, vorlesung


@app.cell(hide_code=True)
def _(SlideCreator, lehrstuhl, presenter, vorlesung):
    sc = SlideCreator(lehrstuhl, vorlesung, presenter)
    return (sc,)


@app.cell
def _(mo, sc):

    basic_supply_mng = sc.create_slide(
        "Basic Supply Management", layout_type="1-column"
    )
    basic_supply_mng.content1 = mo.md(
    """
        For this aggregation task, we assume that all 17 Phoenix distribution centers operate with the same  
    (Q, R) replenishment logic you studied for the DC in Fürth.  
    Knowing each DC’s parameters and its forecasted daily demand lets us anticipate how much they will order  
    from the central warehouse. Our goal is to combine these expected orders to determine the shipments that  
    need to leave the central warehouse.

    We look ahead over a short supplier lead time (3 days) and extend the horizon to the next 10 days to get a  
    stable view of upcoming requirements.

    **Gross requirements over the horizon:**

    \[
    GR_t = \sum_{i=1}^{17} Q_{i,t} \quad   t = 1,\ldots,10  
    \]

    This tells us the total quantity that must be shipped from the central warehouse to cover all DC orders  
    across the planning window.

    """
    )


    return (basic_supply_mng,)


@app.cell(hide_code=True)
def _(basic_supply_mng):
    basic_supply_mng.render_slide()
    return


@app.cell
def _(DataURLs, mo, sc):

    basic_supply_mng2 = sc.create_slide(
        "Basic Supply Management", layout_type="2-row"
    )
    basic_supply_mng2.content1 = mo.md(
    """
    Lets first have a look at the data for the individual DCs.

    """
    )

    import pandas as pd 

    df_supply = pd.read_csv(DataURLs.SUPPLY_PLAN)

    basic_supply_mng2.content2 = mo.ui.table(df_supply[["DC", "Date", "Order_Placed_Qty"]].sort_values(["Date", "DC"])
    )



    return basic_supply_mng2, df_supply


@app.cell
def _(basic_supply_mng2):
    basic_supply_mng2.render_slide()
    return


@app.cell
def _(df_supply, mo, sc):



    basic_supply_mng3 = sc.create_slide(
        "Basic Supply Management", layout_type="2-row"
    )
    basic_supply_mng3.content1 = mo.md(
    """
    Then we aggregate the order quantities of the 16 DCs to get the total GR at the central warebouse.



    """
    )


    basic_supply_mng3.content2 = mo.ui.table(df_supply[["Order_Placed_Qty", "Date"]].groupby(["Date"]).sum())




    return (basic_supply_mng3,)


@app.cell(hide_code=True)
def _(basic_supply_mng3):
    basic_supply_mng3.render_slide()
    return


if __name__ == "__main__":
    app.run()
