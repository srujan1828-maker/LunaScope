"""Prepare verified persistent NASA inputs, then replace this process with the server."""
import os,sys,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from app.core.nasa_data import RAW,readiness


def prepare(auto_fetch=True):
    RAW.mkdir(parents=True,exist_ok=True)
    if auto_fetch:
        subprocess.run([sys.executable,str(ROOT/'backend/scripts/fetch_nasa_data.py')],cwd=ROOT,check=True)
    if not (RAW/'manifest.json').exists():raise RuntimeError('NASA inputs missing. Enable LUNASCOPE_AUTO_FETCH or populate the persistent data directory.')
    expected=json.loads((ROOT/'data/nasa_provenance.json').read_text(encoding='utf-8'))
    actual=json.loads((RAW/'manifest.json').read_text(encoding='utf-8'))
    for name,record in expected['sources'].items():
        if actual['sources'].get(name,{}).get('sha256')!=record['sha256']:
            raise RuntimeError('NASA source identity differs from this release: '+name+'. Review/re-ingest it explicitly before deploying.')
    if not (RAW/'LDEM_80S_80M.npy').exists():
        subprocess.run([sys.executable,str(ROOT/'backend/scripts/prepare_nasa_data.py')],cwd=ROOT,check=True)
    if not readiness()['ready']:raise RuntimeError('Scientific inputs are incomplete: '+str(readiness()['missing_files']))
    from app.core.nasa_data import terrain_grid
    from app.core.spice_geometry import spice
    terrain_grid();spice()
    print('Verified official NASA inputs ready in '+str(RAW),flush=True)


if __name__=='__main__':
    prepare(os.environ.get('LUNASCOPE_AUTO_FETCH','true').lower() in ('1','true','yes'))
    os.environ.setdefault('HOST','0.0.0.0');os.environ.setdefault('PORT','8000')
    os.chdir(ROOT)
    if os.name=='nt':
        # Windows exec argument joining does not quote a project path containing spaces.
        raise SystemExit(subprocess.call([sys.executable,'-u','run.py'],cwd=ROOT))
    os.execv(sys.executable,[sys.executable,'-u','run.py'])
