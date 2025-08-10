from pathlib import Path
from setuptools import setup


def read_requirements(filename: str):
    req_path = Path(__file__).parent / filename
    if not req_path.exists():
        return []
    lines = [
        ln.strip()
        for ln in req_path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    return lines


README = (Path(__file__).parent / "README.md").read_text(encoding="utf-8") if (Path(__file__).parent / "README.md").exists() else ""

setup(
    name="frameextractor",
    version="0.1.0",
    description="Extract video frames via ffmpeg (CLI + tkinter GUI)",
    long_description=README,
    long_description_content_type="text/markdown",
    url="",
    author="",
    python_requires=">=3.9",
    py_modules=["framegrab", "gui_app"],
    install_requires=read_requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            "framegrab=framegrab:main",
            "framegrab-gui=gui_app:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Environment :: Console",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications :: GTK",
        "License :: OSI Approved :: MIT License",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Multimedia :: Video",
        "Intended Audience :: End Users/Desktop",
    ],
)

