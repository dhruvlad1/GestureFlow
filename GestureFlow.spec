# PyInstaller build configuration for the GestureFlow Windows application.

from pathlib import Path

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules


PROJECT_ROOT = Path(SPECPATH)
SOURCE_ROOT = PROJECT_ROOT / "src"
MODEL_FILE = PROJECT_ROOT / "models" / "hand_landmarker.task"


def runtime_data_files(package_name):
    """Collect package data while excluding Python source/bytecode files."""

    return [
        (source, destination)
        for source, destination in collect_data_files(
            package_name,
            include_py_files=False,
        )
        if Path(source).suffix.lower() not in {".py", ".pyc", ".pyi"}
    ]


mediapipe_hiddenimports = (
    [
        "mediapipe.tasks",
        "mediapipe.tasks.python",
    ]
    + collect_submodules("mediapipe.tasks.python.vision")
    + collect_submodules("mediapipe.tasks.python.core")
)
pyautogui_hiddenimports = [
    "pyautogui._pyautogui_win",
]

hiddenimports = sorted(
    set(mediapipe_hiddenimports + pyautogui_hiddenimports)
)

datas = [
    (str(MODEL_FILE), "models"),
]
datas += runtime_data_files("mediapipe")
datas += runtime_data_files("cv2")
datas += runtime_data_files("pyautogui")

binaries = []
binaries += collect_dynamic_libs("mediapipe")
binaries += collect_dynamic_libs("cv2")

analysis = Analysis(
    [str(SOURCE_ROOT / "main.py")],
    pathex=[str(SOURCE_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "IPython",
        "notebook",
        "jupyter",
        "matplotlib",
        "matplotlib.*",
        "tkinter",
        "_tkinter",
        "tcl",
        "tk",
        "mediapipe.tasks.python.benchmark",
        "mediapipe.tasks.python.benchmark.*",
        "mediapipe.tasks.python.test",
        "mediapipe.tasks.python.test.*",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="GestureFlow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    name="GestureFlow",
    strip=False,
    upx=False,
)
