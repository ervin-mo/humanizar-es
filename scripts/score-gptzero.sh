#!/bin/bash
# Mide varios archivos en el AI Detector de GPTZero (declara soporte de espanol).
#
# Notas de implementacion (ver references/detectores.md):
#   - El boton se llama exactamente "Scan" (no "Detect").
#   - El escaneo abre una PAGINA NUEVA en app.gptzero.me; el resultado no esta en p1.
#   - Se limpian los anuncios con un MutationObserver, igual que en ZeroGPT, y el clic
#     se reintenta si no aparece la pagina de resultados.
#   - Recordatorio: GPTZero marca como IA prosa academica humana en espanol. Mide
#     siempre un control humano del mismo registro antes de interpretar el veredicto.
#
# uso: ./score-gptzero.sh archivo1.txt [archivo2.txt ...]
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

for (const p of await task.pages()) {
  if (p.label !== "p1") { try { await p.close(); } catch (e) {} }
}

await page.goto("https://gptzero.me/");
await page.waitForSelector("textarea", { state: "visible" });

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

await page.focus("textarea");
await page.keyboard.paste(text);
await page.waitForTimeout(2000);
const taLen = await page.evaluate(() => document.querySelector("textarea").value.length);
if (!taLen) throw new Error("textarea vacio: el texto no se pego");

let result = null;
for (let intento = 1; intento <= 3 && !result; intento++) {
  await page.evaluate(() => window.__quitarAnuncios && window.__quitarAnuncios());
  const g = await page.evaluate(() => {
    const b = [...document.querySelectorAll("button")].find((x) => /^Scan\$/i.test(x.innerText.trim()));
    if (!b) throw new Error("no hay boton Scan");
    b.scrollIntoView({ block: "center" });
    const r = b.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
  });
  await page.mouse.click(g.x, g.y, { label: "escanear gptzero" });
  for (let i = 0; i < 12; i++) {
    await page.waitForTimeout(2500);
    const ps = (await task.pages()).filter((p) => p.label !== "p1");
    if (ps.length) { result = ps[ps.length - 1]; break; }
    const url = await page.url();
    if (/app\\.gptzero\\.me/.test(url)) { result = page; break; }
  }
  if (!result) console.log("  intento " + intento + " sin pagina de resultados, reintento...");
}
if (!result) throw new Error("no aparecio la pagina de resultados tras 3 intentos");
await result.waitForLoadState();

// huella del texto enviado: sirve para confirmar que el resultado leido es el de ESTE
// archivo y no una pagina de resultados vieja o de otro escaneo.
const huella = text.replace(/\s+/g, " ").trim().slice(20, 70);

let v = null;
let coincide = false;
for (let i = 0; i < 45; i++) {
  const r = await result.evaluate((h) => {
    const t = document.body.innerText;
    const m = t.match(/(We are highly confident this text was AI generated|We are highly confident this text is entirely human|[^\n]{0,60}likely to be[^\n]{0,60})/i);
    const human = t.match(/Human\s+(\d{1,3})%/i);
    return {
      veredicto: m ? m[0].trim().replace(/\s+/g, " ") : null,
      humano: human ? human[1] + "%" : null,
      contieneTexto: t.replace(/\s+/g, " ").includes(h),
    };
  }, huella);
  if (r.veredicto) {
    v = r;
    coincide = r.contieneTexto;
    if (coincide) break;
  }
  await result.waitForTimeout(2000);
}
if (v && !coincide) {
  console.log("  AVISO: el resultado no contiene el texto enviado; puede ser una pagina vieja");
}
if (!v || !v.veredicto) {
  console.log("CHARS " + taLen + " | SIN VEREDICTO (puede requerir sesion o haber limite)");
} else {
  console.log("CHARS " + taLen + " | humano " + v.humano + " | " + v.veredicto + (coincide ? "" : "  [SIN CONFIRMAR]"));
}
try { if (result !== page) await result.close(); } catch (e) {}
await task.finish({ keep: [] });
EOF
done
[ "$FALLOS" -eq 0 ] || echo "($FALLOS archivo(s) sin medir)"
exit $(( FALLOS > 0 ))
