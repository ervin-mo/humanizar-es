#!/bin/bash
# Mide un archivo en el AI Detector de Grammarly.
#
# ATENCION: Grammarly limita los escaneos gratuitos por IP. Tras el primero, el boton
# "Scan for AI" deja de arrancar el escaneo sin mostrar ningun error. Para medir varias
# veces hay que tener la sesion iniciada en Grammarly dentro del navegador de
# ego-browser (con sesion, los escaneos son ilimitados). Ver references/detectores.md.
#
# uso: ./score-grammarly.sh ruta/al/archivo.txt
set -u
if [ $# -ne 1 ] || [ ! -f "$1" ]; then
  echo "uso: $(basename "$0") archivo.txt   (un solo archivo por corrida)"; exit 2
fi
command -v ego-browser >/dev/null 2>&1 || { echo "ERROR: falta ego-browser (ver references/detectores.md)"; exit 2; }
FILE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
# la ruta viaja como literal JSON: el proceso de ego-browser no hereda el entorno ni el cwd
RUTA_JS="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$FILE")"
ego-browser nodejs <<EOF
const fs = await import("node:fs/promises");
const text = await fs.readFile(${RUTA_JS}, "utf8");
const task = await taskSpace("humanizar-es medicion");
const page = task.page("p1");

await page.goto("https://www.grammarly.com/ai-detector");
await page.waitForSelector('textarea[name="toolInput"]', { state: "visible" });
await page.waitForTimeout(1500);

// quitar anuncios y banners que interceptan los clics
await page.evaluate(() => {
  const sels = 'iframe[id*="google_ads"], ins.adsbygoogle, div[id*="google_vignette"], ' +
               'div[id*="aswift"], iframe[id*="aswift"], iframe[title*="advert"]';
  document.querySelectorAll(sels).forEach((e) => e.remove());
});

await page.focus('textarea[name="toolInput"]');
await page.keyboard.paste(text);
await page.waitForTimeout(1500);
const taLen = await page.evaluate(() => document.querySelector('textarea[name="toolInput"]').value.length);
if (!taLen) throw new Error("textarea vacio: el texto no se pego");

// localizar el boton por ref del snapshot (el locator semantico no lo resuelve)
const snap = await page.snapshot();
const idx = snap.indexOf("Scan for AI");
const refs = idx < 0 ? [] : [...snap.slice(0, idx).matchAll(/ref=(\d+)/g)];
const ref = refs.length ? "@" + refs[refs.length - 1][1] : null;

try {
  if (!ref) throw new Error("no encontre el boton en el snapshot");
  await page.click(ref, { timeout: 15000 });
} catch (e) {
  console.log("aviso: click por ref fallo (" + String(e).slice(0, 80) + "), intento por coordenadas");
  const g = await page.evaluate(() => {
    const b = [...document.querySelectorAll("button")].find((x) => /Scan for AI/i.test(x.innerText));
    if (!b) throw new Error("no hay boton Scan for AI");
    b.scrollIntoView({ block: "center" });
    const r = b.getBoundingClientRect();
    return { x: Math.round(r.x + 8), y: Math.round(r.y + r.height / 2) };
  });
  await page.mouse.click(g.x, g.y, { label: "escanear" });
}

// OJO: el estado inicial ya contiene "—% of this text appears to be AI-generated",
// asi que hay que exigir digitos y ausencia del em-dash o devuelve el placeholder.
await page.waitForTimeout(3000);
await page.waitForFunction(() => {
  const t = document.body.innerText;
  return /[0-9]+% of this text appears to be AI-generated/.test(t) && !/—%/.test(t);
}, undefined, { timeout: 200000 });
await page.waitForTimeout(1200);

const out = await page.evaluate(() => {
  const t = document.body.innerText;
  const i = t.indexOf("AI Detection results");
  return t.slice(i, i + 180).replace(/\n+/g, " | ");
});
console.log("CHARS " + taLen + " | SCORE >> " + out);
await task.finish({ keep: [] });
EOF
