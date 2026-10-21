#!/usr/bin/env python3
"""Reuse exact checksum-pinned EMU binaries. No Mesa rebuild; no driver in noexec filesDir."""
import hashlib,json,subprocess,sys,zipfile,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent

def package(cache,jni,assets):
    catalog=json.loads((HERE/'gpu_drivers.json').read_text())
    cache,jni,assets=map(Path,(cache,jni,assets))
    for d in (cache,jni,assets/'gpu-licenses'):d.mkdir(parents=True,exist_ok=True)
    for e in catalog['drivers']:
        archive=cache/e['archive']
        if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest()!=e['sha256']:
            subprocess.run(['curl','-fL','--retry','3','--connect-timeout','25','--max-time','360','-o',str(archive),e['url']],check=True)
        assert hashlib.sha256(archive.read_bytes()).hexdigest()==e['sha256'],e['id']+' checksum mismatch'
        with zipfile.ZipFile(archive) as z:
            names=z.namelist()
            lib='libvulkan_panfrost.so' if e['kind']=='panvk' else json.loads(z.read('meta.json'))['libraryName']
            assert '/' not in lib and '\\' not in lib
            matches=[n for n in names if n.rsplit('/',1)[-1]==lib]
            assert len(matches)==1,(e['id'],lib)
            data=z.read(matches[0]);assert 200000<len(data)<180*1024*1024
            assert data[:5]==b'\x7fELF\x02' and int.from_bytes(data[18:20],'little')==183
            (jni/e['library']).write_bytes(data)
            # G52's libdrm is private to its custom namespace. Keep Blender's NDK30 libc++.
            for name in names:
                base=name.rsplit('/',1)[-1]
                if base=='libdrm.so':
                    dep=z.read(name)
                    out=jni/'libdrm.so'
                    if out.exists():assert out.read_bytes()==dep,'Conflicting libdrm versions'
                    else:out.write_bytes(dep)
                if any(w in base.lower() for w in ('license','notice','copying','meta.json')) and not name.endswith('/'):
                    (assets/'gpu-licenses'/(e['id']+'-'+base)).write_bytes(z.read(name))
            # Stock upstream packager needs a primary driver, but runtime selection is explicit.
            if e['id']=='a840_h29':shutil.copyfile(jni/e['library'],cache/'libvulkan_turnip.so')
        e['binarySha256']=hashlib.sha256(data).hexdigest()
        print('Verified GPU:',e['id'],flush=True)
    (assets/'drnas_gpu_drivers.json').write_text(json.dumps(catalog,indent=2)+'\n')
    return catalog

if __name__=='__main__':package(*sys.argv[1:])
