default: dev

format:
    uv run ruff format

dev:
    uv run pyxel-reload main

build:
    rm -rf pyxel_utils/
    cp -R $(uv run python -c "import pyxel_utils; print(pyxel_utils.__path__[0])") .
    uv run pyxel package . main.py
    uv run pyxel app2html gravimory.pyxapp
    rm -rf pyxel_utils/ gravimory.pyxapp
    echo {{GREEN}}"Final build is in gravimory.html"

build-font:
    # KarenFat from https://www.pentacom.jp/pentacom/bitfontmaker2/gallery/?id=346
    nix run nixpkgs#otf2bdf -- -l "20_126" -r 72 -n -p 18 ~/Downloads/KarenFat.ttf -o font-18.bdf || true
    nix run nixpkgs#otf2bdf -- -l "20_126" -r 72 -n -p 32 ~/Downloads/KarenFat.ttf -o font-32.bdf || true
