"""
Cifra las fotos de la boda para publicarlas en GitHub Pages.

Uso (en Windows, desde la carpeta del proyecto):
    py cifrar.py "C:\\Users\\DELL\\Pictures\\boda"

Crea la carpeta "datos" junto a este archivo con:
    datos/config.json    sal y parámetros (no secretos)
    datos/manifest.bin   lista de fotos, cifrada
    datos/t/0001.bin     miniatura cifrada (400 px)
    datos/p/0001.bin     vista para revisar cifrada (1800 px)
    datos/o/0001.bin     original cifrado (para la descarga)

Requisitos:  py -m pip install cryptography pillow
"""
import argparse, base64, getpass, io, json, os, re, shutil, sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Faltan librerías. Ejecuta:  py -m pip install cryptography pillow")

EXTS = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
ITERATIONS = 310_000
PAGES_LIMIT = 1_000_000_000      # GitHub Pages: 1 GB por sitio
FILE_LIMIT = 100_000_000         # GitHub: 100 MB por archivo


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
    return kdf.derive(password.encode("utf-8"))


def encrypt(aes: AESGCM, data: bytes) -> bytes:
    iv = os.urandom(12)
    return iv + aes.encrypt(iv, data, None)   # iv(12) + texto cifrado + etiqueta(16)


def resized_jpeg(im: Image.Image, max_side: int, quality: int) -> bytes:
    copy = im.copy()
    copy.thumbnail((max_side, max_side), Image.LANCZOS)
    buf = io.BytesIO()
    copy.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description="Cifra las fotos de la boda para GitHub Pages")
    ap.add_argument("carpeta", help="Carpeta con las fotos")
    ap.add_argument("--max-original", type=int, default=0,
                    help="Reduce los originales a este lado máximo en px (ej. 4000) si no caben en 1 GB")
    args = ap.parse_args()

    src = Path(args.carpeta)
    if not src.is_dir():
        sys.exit(f"No encuentro la carpeta: {src}")

    def natural(p):  # orden 1, 2, 10 en vez de 1, 10, 2
        return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(p.relative_to(src)).lower())]
    files = sorted([p for p in src.rglob("*") if p.suffix.lower() in EXTS], key=natural)
    if not files:
        sys.exit("No encontré fotos .jpg, .png o .webp en esa carpeta.")
    print(f"Encontré {len(files)} fotos.")

    password = os.environ.get("BODA_PASSWORD")
    if not password:
        password = getpass.getpass("Contraseña para el sitio (no se ve al escribir): ")
        if getpass.getpass("Repite la contraseña: ") != password:
            sys.exit("Las contraseñas no coinciden.")
    if len(password) < 10:
        print("Aviso: usa una frase de 10 caracteres o más. Las fotos cifradas serán públicas en GitHub.")

    out = Path(__file__).resolve().parent / "datos"
    if out.exists():
        shutil.rmtree(out)
    for sub in ("t", "p", "o"):
        (out / sub).mkdir(parents=True)

    salt = os.urandom(16)
    aes = AESGCM(derive_key(password, salt))
    manifest, total, big = [], 0, []

    for i, path in enumerate(files, 1):
        pid = f"{i:04d}"
        raw = path.read_bytes()
        mime = EXTS[path.suffix.lower()]
        try:
            with Image.open(io.BytesIO(raw)) as im0:
                im = ImageOps.exif_transpose(im0).convert("RGB")
        except Exception as e:
            print(f"  [{pid}] Omitida, no se pudo leer {path.name}: {e}")
            continue

        original = raw
        if args.max_original and max(im.size) > args.max_original:
            original = resized_jpeg(im, args.max_original, 90)
            mime = "image/jpeg"

        parts = {
            "t": encrypt(aes, resized_jpeg(im, 400, 72)),
            "p": encrypt(aes, resized_jpeg(im, 1800, 82)),
            "o": encrypt(aes, original),
        }
        for sub, blob in parts.items():
            (out / sub / f"{pid}.bin").write_bytes(blob)
            total += len(blob)
            if len(blob) > FILE_LIMIT:
                big.append(path.name)

        name = path.name if args.max_original == 0 or mime == EXTS[path.suffix.lower()] else path.stem + ".jpg"
        manifest.append({"id": pid, "name": name, "type": mime, "size": len(original)})
        print(f"  [{pid}] {path.name}  ({len(raw)/1e6:.1f} MB)")

    (out / "manifest.bin").write_bytes(encrypt(aes, json.dumps(manifest, ensure_ascii=False).encode("utf-8")))
    (out / "config.json").write_text(json.dumps({
        "v": 1, "kdf": "PBKDF2-SHA256", "iterations": ITERATIONS,
        "salt": base64.b64encode(salt).decode(), "count": len(manifest)
    }, indent=2))

    print(f"\nListo: {len(manifest)} fotos cifradas en {out}")
    print(f"Tamaño total: {total/1e9:.2f} GB")
    if big:
        print("ERROR: estos archivos pasan de 100 MB y GitHub no los acepta:", ", ".join(big))
    if total > PAGES_LIMIT:
        print("AVISO: pasa de 1 GB, el límite de GitHub Pages.")
        print("Vuelve a correrlo reduciendo los originales, por ejemplo:")
        print(f'  py cifrar.py "{src}" --max-original 4000')


if __name__ == "__main__":
    main()
