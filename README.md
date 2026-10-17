# Fotos de la boda

Sitio para revisar las fotos de la boda deslizando: a la derecha se quedan, a la izquierda van a la papelera. Al final se descargan las elegidas en ZIP, con los archivos originales.

Las fotos se suben a GitHub **cifradas** con la contraseña. En el repositorio solo hay archivos `.bin` ilegibles; la página los descifra en el navegador cuando alguien escribe la contraseña correcta.

## Contenido

| Archivo | Qué es |
|---|---|
| `index.html` | El sitio |
| `cifrar.py` | Cifra tus fotos y crea la carpeta `datos/` |
| `.nojekyll` | Le dice a GitHub Pages que publique los archivos tal cual |

## 1. Cifrar las fotos (una vez, en tu compu)

1. Instala Python desde python.org (marca "Add Python to PATH").
2. Abre una terminal en esta carpeta e instala las librerías:
   ```
   py -m pip install cryptography pillow
   ```
3. Cifra la carpeta de la boda:
   ```
   py cifrar.py "C:\Users\DELL\Pictures\boda"
   ```
   Te pedirá la contraseña dos veces. Usa una **frase larga** (por ejemplo, cuatro palabras), porque los archivos cifrados serán públicos y una contraseña corta se puede adivinar con fuerza bruta.

Al terminar te dice cuánto pesa todo. GitHub Pages admite **1 GB por sitio**. Si te pasas, vuelve a correrlo reduciendo los originales:
```
py cifrar.py "C:\Users\DELL\Pictures\boda" --max-original 4000
```

Cada vez que lo corres se borra y se rehace `datos/` con una contraseña nueva.

## 2. Probar en tu compu (opcional)

El navegador no deja descifrar desde un archivo abierto con doble clic. Levanta un servidor local:
```
py -m http.server 8000
```
y abre http://localhost:8000

## 3. Subir a GitHub

1. Crea un repositorio nuevo en github.com (puede ser público: las fotos van cifradas).
2. Sube esta carpeta completa con **GitHub Desktop** (la subida desde la web solo acepta 100 archivos a la vez).
3. En el repo: **Settings → Pages → Branch: main / (root) → Save**.
4. En unos minutos queda en `https://TU-USUARIO.github.io/NOMBRE-DEL-REPO/`.

## Notas

- La foto de la portada sí es pública (se ve antes de la contraseña).
- Las elecciones se guardan en cada navegador. Si tú y Nadya revisan en compus distintas, cada quien tendrá su propia selección.
- Formatos admitidos: JPG, PNG y WEBP. Las fotos HEIC del iPhone hay que convertirlas antes.
- Sin la carpeta `datos/`, el sitio abre en modo demostración con la contraseña `boda2026`.
