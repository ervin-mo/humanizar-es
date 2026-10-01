# Cambios

## 1.2.0 — 30 de septiembre de 2026

- **El cubo** (`scripts/cubo.py`): reescritura oración por oración guiada por un detector
  local. Llevó un párrafo de 100% IA a 0% en Grammarly y 99% humano en CleverHumanizer.
  Trabaja párrafo por párrafo por defecto; `--texto-completo` gira todo a la vez.
- Detector local (`scripts/sustituto.py`): Binoculars + Fast-DetectGPT sobre Qwen2.5.
- Revisor de sentido: otro modelo veta los giros que cambian, inventan o no tienen lógica.
- Varias familias de generadores (`HUMANIZAR_MODEL="a,b"`) y aviso de palabras repetidas.
- `scripts/calibrar.py`: mide qué tan bien predice el detector local a tu detector.
- `scripts/ruleta.py`: sinónimos guiados por detector (opcional; no movió a Grammarly).
- La skill funciona en Claude Code, Codex, OpenCode, Antigravity y DeepSeek Harness;
  `install.sh` instala por defecto en `~/.claude/skills` y `~/.agents/skills`.
- CPU por defecto: en Mac, la GPU traba la pantalla.

## 1.1.0 — 30 de septiembre de 2026

- `scripts/estilo.py` (sin dependencias) y `verificar_fidelidad.py` configurable, con
  detección de negaciones perdidas.
- Benchmark revisado con dos rondas de refutación; resultados de Grammarly.

## 1.0.0

- Guía de reescritura, benchmark inicial y scripts de medición.
