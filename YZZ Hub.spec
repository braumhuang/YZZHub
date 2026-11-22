# -*- mode: python ; coding: utf-8 -*-
r"""YZZ Hub Windows one-file build spec (PyInstaller 4.10+).

Build entry used by build_win.bat:

    python -m PyInstaller --noconfirm --clean --distpath dist --workpath build "YZZ Hub.spec"

Why a spec file instead of command-line arguments
-------------------------------------------------
PyInstaller scans binary dependencies in the order
``[dir of the binary] + sys.path + System32 + PATH``. The VC++ runtime
DLLs (msvcp140*.dll / vcruntime140*.dll) therefore come from
``C:\Windows\System32`` whenever it has them -- which is the case on
GitHub Actions runners (they ship the latest VC++ 2015-2022 redist),
but usually NOT on an unmodified Windows 7 box. Those latest runtime
DLLs import the ``_o_*`` exports that only newer Universal CRTs provide,
so an exe built on such a runner dies on an updated-to-old-UCRT Windows 7
machine with exactly::

    ImportError: DLL load failed while importing QtCore: 找不到指定的程序

Building on the local Windows 7 machine works because System32 there has
no (or only an old) VC++ runtime, so PyInstaller falls back to the copies
shipped inside the PyQt5 wheel (PyQt5\Qt5\bin, version 14.26.28720.3),
whose import tables only reference the classic UCRT symbols.

The pinning step below replaces every VC++ runtime DLL in the bundle with
the copy from PyQt5\Qt5\bin, making the exe byte-comparable no matter
where it was built (local Windows 7 or any CI runner) and compatible
with Windows 7 SP1 through Windows 11.
"""

import os

PROJECT = SPECPATH  # directory that contains this spec file

a = Analysis(
    [os.path.join(PROJECT, 'main.py')],
    pathex=[PROJECT],
    binaries=[],
    datas=[(os.path.join(PROJECT, 'assets'), 'assets')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure, a.zipped_data)

# ---------------------------------------------------------------------------
# Pin the VC++ runtime to the Win7-compatible copies shipped in the PyQt5
# wheel (PyQt5\Qt5\bin). Their import tables were verified to reference only
# classic Universal CRT symbols (no ``_o_*``), so they work on the original
# Windows 7 UCRT as well as on modern Windows.
# ---------------------------------------------------------------------------
if os.name == 'nt':
    import PyQt5

    _pyqt_dir = os.path.dirname(PyQt5.__file__)
    _qt_bin = None
    for _sub in ('Qt5', 'Qt'):
        _cand = os.path.join(_pyqt_dir, _sub, 'bin')
        if os.path.isfile(os.path.join(_cand, 'Qt5Core.dll')):
            _qt_bin = _cand
            break
    if _qt_bin is None:
        raise SystemExit(
            '[ERROR] Cannot locate the Qt binary directory of the installed '
            'PyQt5 package; unable to pin the Win7-compatible VC++ runtime.'
        )

    _pin = {}
    for _fn in os.listdir(_qt_bin):
        _low = _fn.lower()
        if _low.startswith(('msvcp140', 'vcruntime140')) and _low.endswith('.dll'):
            _pin[_low] = os.path.join(_qt_bin, _fn)

    for _required in ('msvcp140.dll', 'msvcp140_1.dll', 'vcruntime140.dll', 'vcruntime140_1.dll'):
        if _required not in _pin:
            raise SystemExit(
                '[ERROR] PyQt5 wheel does not ship %s in %s; cannot pin the '
                'Win7-compatible VC++ runtime.' % (_required, _qt_bin)
            )

    _seen_names = set()
    for _i in range(len(a.binaries)):
        _dest, _src = a.binaries[_i][0], a.binaries[_i][1]
        _base = os.path.basename(_dest.replace('\\', '/')).lower()
        if _base in _pin and ('\\' not in _dest) and ('/' not in _dest):
            # Root-level VC++ runtime entry: replace the source file with the
            # copy from PyQt5\Qt5\bin while keeping the destination name.
            print('[INFO] Pinning %s: %s -> %s' % (_dest, _src, _pin[_base]))
            a.binaries[_i] = tuple([_dest, _pin[_base]] + list(a.binaries[_i][2:]))
            _seen_names.add(_base)

    # Also ship pin candidates that the dependency walk did not reference,
    # so that runtime neighbours (e.g. msvcp140_2.dll used by other Qt
    # components) always match the pinned series.
    for _base in sorted(_pin):
        if _base not in _seen_names:
            print('[INFO] Adding pinned VC++ runtime: %s' % _pin[_base])
            a.binaries.append((_base, _pin[_base], 'BINARY'))
            _seen_names.add(_base)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YZZ Hub',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(PROJECT, 'assets', 'icon.ico'),
    version=os.path.join(PROJECT, 'version_info.txt'),
)
