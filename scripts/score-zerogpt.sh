#!/bin/bash
# Mide varios archivos en el AI Detector de ZeroGPT.
#
# Notas de implementacion (aprendidas midiendo, ver references/detectores.md):
#   - Las rutas se convierten a absolutas: el proceso Node de ego-browser no hereda el
#     cwd del shell.
#   - ZeroGPT inyecta un anuncio interstitial de Google (#google_vignette) que intercepta
#     el clic y hace que el escaneo nunca arranque, sin mensaje de error. Ademas se
#     inyecta DESPUES de la carga, asi que una limpieza unica no basta: se instala un
#     MutationObserver que los elimina en cuanto aparecen.
#   - Aun asi puede fallar, asi que hay reintentos del clic.
#
# uso: ./score-zerogpt.sh archivo1.txt [archivo2.txt ...]
set -u
FALLOS=0
if [ $# -eq 0 ]; then
  echo "uso: $(basename "$0") archivo1.txt [archivo2.txt ...]"; exit 2
fi
command -v ego-browser >/dev/null 2>&1 || { echo "ERROR: falta ego-browser (ver references/detectores.md)"; exit 2; }
for ARG in "$@"; do
  [ -f "$ARG" ] || { echo "ERROR: no existe $ARG"; FALLOS=$((FALLOS + 1)); continue; }
  FILE="$(cd "$(dirname "$ARG")" && pwd)/$(basename "$ARG")"
  # la ruta viaja como literal JSON: el proceso de ego-browser no hereda el entorno
  # ni el cwd, y una ruta con comillas o $ romperia el JavaScript si se pega tal cual
  RUTA_JS="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$FILE")"
  echo "----- $(basename "$FILE")"
  ego-browser nodejs <<EOF || FALLOS=$((FALLOS + 1))
const fs = await import("node:fs/promises");
const text = await fs.readFile(${RUTA_JS}, "utf8");
const task = await taskSpace("humanizar-es medicion");
const page = task.page("p1");

await page.goto("https://www.zerogpt.com/");
await page.waitForSelector('textarea[name="textArea"]', { state: "visible" });

// observador que elimina anuncios de forma continua
await page.evaluate(() => {
  window.__quitarAnuncios = () => {
    const sels = 'iframe[id*="google_ads"], ins.adsbygoogle, div[id*="google_vignette"], ' +
                 'div[id*="aswift"], iframe[id*="aswift"]';
    document.querySelectorAll(sels).forEach((e) => e.remove());
  };
  window.__quitarAnuncios();
  if (!window.__obsAds) {
    window.__obsAds = new MutationObserver(() => window.__quitarAnuncios());
    window.__obsAds.observe(document.documentElement, { childList: true, subtree: true });
  }
});

await page.focus('textarea[name="textArea"]');
await page.keyboard.paste(text);
await page.waitForTimeout(1500);
const taLen = await page.evaluate(() => document.querySelector('textarea[name="textArea"]').value.length);
if (!taLen) throw new Error("textarea vacio: el texto no se pego");

// clic con reintentos: el anuncio puede volver a inyectarse entre intento e intento
let listo = false;
for (let intento = 1; intento <= 3 && !listo; intento++) {
  await page.evaluate(() => window.__quitarAnuncios && window.__quitarAnuncios());
  const g = await page.evaluate(() => {
    const b = [...document.querySelectorAll("button")].find((x) => /Detect Text/i.test(x.innerText));
    if (!b) throw new Error("no hay boton Detect Text");
    b.scrollIntoView({ block: "center" });
    const r = b.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
  });
  await page.mouse.click(g.x, g.y, { label: "detectar zerogpt" });
  for (let i = 0; i < 10; i++) {
    await page.waitForTimeout(2500);
    if (await page.evaluate(() => /Your Text is/i.test(document.body.innerText))) { listo = true; break; }
  }
  if (!listo) console.log("  intento " + intento + " sin veredicto, reintento...");
}
if (!listo) throw new Error("no aparecio el veredicto tras 3 intentos (posible limite de uso)");

await page.waitForTimeout(2500);

// el score es el PRIMER porcentaje que aparece DESPUES del veredicto.
// Los otros (98.4%, <1%, 30%) son estadisticas de marketing y descuentos.
const out = await page.evaluate(() => {
  const t = document.body.innerText;
  const m = t.match(/Your Text is[^\n]{0,80}/i);
  if (!m) return { veredicto: "?", score: "?" };
  const resto = t.slice(t.indexOf(m[0]) + m[0].length);
  const p = resto.match(/(\d{1,3}(?:\.\d+)?)\s*%/);
  return { veredicto: m[0].trim().replace(/\s+/g, " "), score: p ? p[1] + "%" : "?" };
});
console.log("CHARS " + taLen + " | IA " + out.score + " | " + out.veredicto);
await task.finish({ keep: [] });
EOF
done
[ "$FALLOS" -eq 0 ] || echo "($FALLOS archivo(s) sin medir)"
exit $(( FALLOS > 0 ))
