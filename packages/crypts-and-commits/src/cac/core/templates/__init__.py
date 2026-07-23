from importlib import resources


def load(package: str, filename: str) -> str:
    return resources.files(f"{__name__}.{package}").joinpath(filename).read_text(encoding="utf-8")
