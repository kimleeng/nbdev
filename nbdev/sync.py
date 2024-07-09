# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/06_sync.ipynb.

# %% auto 0
__all__ = ['absolute_import', 'nbdev_update']

# %% ../nbs/api/06_sync.ipynb 3
from .imports import *
from .config import *
from .maker import *
from .process import *
from .process import _partition_cell
from .export import *
from .doclinks import _iter_py_cells

from execnb.nbio import *
from fastcore.script import *
from fastcore.xtras import *

import ast
from importlib import import_module

# %% ../nbs/api/06_sync.ipynb 5
def absolute_import(name, fname, level):
    "Unwarps a relative import in `name` according to `fname`"
    if not level: return name
    mods = fname.split(os.path.sep)
    if not name: return '.'.join(mods)
    return '.'.join(mods[:len(mods)-level+1]) + f".{name}"

# %% ../nbs/api/06_sync.ipynb 7
@functools.lru_cache(maxsize=None)
def _mod_files():
    midx = import_module(f'{get_config().lib_path.name}._modidx')
    return L(files for mod in midx.d['syms'].values() for _,files in mod.values()).unique()

# %% ../nbs/api/06_sync.ipynb 8
_re_import = re.compile(r"from\s+\S+\s+import\s+\S")

# %% ../nbs/api/06_sync.ipynb 10
def _to_absolute(code, py_path, lib_dir):
    if not _re_import.search(code): return code
    res = update_import(code, ast.parse(code).body, str(py_path.relative_to(lib_dir).parent), absolute_import)
    return ''.join(res) if res else code

# %% ../nbs/api/06_sync.ipynb 11
def _update_nb(nb_path, cells, lib_dir):
    "Update notebook `nb_path` with contents from `cells`"
    nbp = NBProcessor(nb_path, ExportModuleProc(), rm_directives=False)
    nbp.process()
    for cell in cells:
        assert cell.nb_path == nb_path
        nbcell = nbp.nb.cells[cell.idx]
        dirs,_ = _partition_cell(nbcell, 'python')
        nbcell.source = ''.join(dirs) + _to_absolute(cell.code, cell.py_path, lib_dir)
    write_nb(nbp.nb, nb_path)

# %% ../nbs/api/06_sync.ipynb 12
def _update_mod(py_path, lib_dir):
    "Propagate changes from cells in module `py_path` to corresponding notebooks"
    py_cells = L(_iter_py_cells(py_path)).filter(lambda o: o.nb != 'auto')
    for nb_path,cells in groupby(py_cells, 'nb_path').items(): _update_nb(nb_path, cells, lib_dir)

# %% ../nbs/api/06_sync.ipynb 14
@call_parse
def nbdev_update(fname:str=None): # A Python file name to update
    "Propagate change in modules matching `fname` to notebooks that created them"
    if fname and fname.endswith('.ipynb'): raise ValueError("`nbdev_update` operates on .py files.  If you wish to convert notebooks instead, see `nbdev_export`.")
    if os.environ.get('IN_TEST',0): return
    cfg = get_config()
    fname = Path(fname or cfg.lib_path)
    lib_dir = cfg.lib_path.parent
    files = globtastic(fname, file_glob='*.py', skip_folder_re='^[_.]').filter(lambda x: str(Path(x).absolute().relative_to(lib_dir) in _mod_files()))
    files.map(_update_mod, lib_dir=lib_dir)
