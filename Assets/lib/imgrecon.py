import re, unitypack
from unitypack.export import OBJMesh
from UnityPy import AssetsManager
from PIL import Image

VR = re.compile(r'v ')
TR = re.compile(r'vt ')
SR = re.compile(r' ')
def recon(src, mesh):
    sx, sy = src.size
    c = map(SR.split, list(filter(TR.match, mesh))[1::2])
    p = map(SR.split, list(filter(VR.match, mesh))[1::2])
    c = [(round(float(a[1])*sx), round(float(a[2])*sy)) for a in c]
    p = [(-int(float(a[1])), int(float(a[2]))) for a in p]
    my = max(y for x, y in p)
    p = [(x, my-y) for x, y in p[::2]]
    cp = [(l+r, p) for l, r, p in zip(c[::2], c[1::2], p)]
    ox, oy = zip(*[(r-l+p, b-t+q) for (l, t, r, b), (p, q) in cp])
    out = Image.new('RGBA', (max(ox), max(oy)))
    for c, p in cp: out.paste(src.crop(c), p)
    return out

def load_mesh(filepath, require_name=None):
	with open(filepath, 'rb') as ab:
		try:
			bundle = unitypack.load(ab)
			for asset in bundle.assets:
				try:
					for _, obj in asset.objects.items():
						if not obj.type == 'Mesh': continue
						try:
							objdata = obj.read()
							if require_name:
								if objdata.name != require_name:
									continue
							mesh = OBJMesh(objdata).export().splitlines()
							return mesh
						except: pass
				except: pass # just catching errors from unitypack
		except: return None

def load_images(filepath: str):
	am = AssetsManager(filepath)
	for asset in am.assets.values():
		for obj in asset.objects.values():
			if obj.type == "Texture2D":
				yield obj.read()