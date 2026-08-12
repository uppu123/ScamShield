import os
import shutil
import urllib.request

OUT = "data/raw/emscad.csv"
KAGGLE_DATASET = "shivamb/emscad-employment-scam-classification-dataset"

MIRRORS = [
    "https://raw.githubusercontent.com/Erfaniaa/fake-job-posting-prediction/master/dataset.csv",
    "https://raw.githubusercontent.com/martin-vb/emscad/main/data/emscad_v1.csv",
    "https://raw.githubusercontent.com/fivethirtyeight/data/master/emscad/emscad.csv",
]


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    try:
        import kagglehub

        path = kagglehub.dataset_download(KAGGLE_DATASET)
        for name in os.listdir(path):
            if name.lower().endswith(".csv"):
                shutil.copy(os.path.join(path, name), OUT)
                print(f"Saved dataset to {OUT}")
                return
    except Exception as exc:
        print(f"kagglehub failed ({exc}) - trying mirrors")
    for url in MIRRORS:
        try:
            print(f"Downloading {url}")
            urllib.request.urlretrieve(url, OUT)
            print(f"Saved dataset to {OUT}")
            return
        except Exception as exc:
            print(f"Failed {url}: {exc}")
    print(
        "Manual download needed. Get EMSCAD from Kaggle "
        f"({KAGGLE_DATASET}) and place it at {OUT}."
    )


if __name__ == "__main__":
    main()
