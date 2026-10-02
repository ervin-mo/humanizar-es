"""Pruebas sin red ni modelos. Corren con la biblioteca estandar:

    python3 -m unittest discover -s tests -v
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(RAIZ, "scripts")
EJ = os.path.join(RAIZ, "ejemplos")
ORIGINAL = os.path.join(EJ, "original.txt")
HIP = os.path.join(EJ, "1-hip.txt")
FINAL = os.path.join(EJ, "2-final.txt")
CONCEPTOS = os.path.join(EJ, "conceptos.txt")

sys.path.insert(0, SCRIPTS)
import hip  # noqa: E402
import unir  # noqa: E402
import verificar_fidelidad as vf  # noqa: E402


def correr(*args, **kw):
    return subprocess.run(args, capture_output=True, text=True, cwd=RAIZ, **kw)


def leer(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return fh.read()


class Fidelidad(unittest.TestCase):
    def test_el_ejemplo_conserva_todos_los_conceptos(self):
        r = correr(sys.executable, os.path.join(SCRIPTS, "verificar_fidelidad.py"),
                   ORIGINAL, HIP, FINAL, "--conceptos", CONCEPTOS)
        self.assertIn("1-hip.txt                      27/27 = 100%", r.stdout)
        self.assertIn("2-final.txt                    27/27 = 100%", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_detecta_concepto_perdido_y_negacion_invertida(self):
        with tempfile.TemporaryDirectory() as tmp:
            malo = os.path.join(tmp, "malo.txt")
            with open(malo, "w", encoding="utf-8") as fh:
                fh.write(leer(ORIGINAL).replace("Heidegger", "un filósofo")
                         .replace("principio de no contradicción", "principio de contradicción"))
            r = correr(sys.executable, os.path.join(SCRIPTS, "verificar_fidelidad.py"),
                       ORIGINAL, malo, "--conceptos", CONCEPTOS)
            self.assertEqual(r.returncode, 1)
            self.assertIn("PERDIDO", r.stdout)
            self.assertIn("«no contradiccion»", r.stdout)

    def test_ignora_acentos_y_forma_unicode(self):
        texto_nfd = unicodedata.normalize("NFD", "La Crítica de la razón pura de Kant")
        self.assertTrue(vf.patron("critica de la razon pura").search(vf.norm(texto_nfd)))

    def test_palabra_completa_y_prefijo(self):
        self.assertFalse(vf.patron("ser").search(vf.norm("el servicio")))
        self.assertTrue(vf.patron("antinomia").search(vf.norm("las antinomias")))
        self.assertTrue(vf.patron("subatómic*").search(vf.norm("nivel subatómico")))

    def test_extraccion_automatica(self):
        nombres = [n for n, _ in vf.extraer_conceptos(leer(ORIGINAL))]
        for esperado in ("Aristóteles", "Tomás de Aquino", "Dasein"):
            self.assertIn(esperado, nombres)
        self.assertNotIn("El", nombres)

    def test_archivo_inexistente_sale_con_dos(self):
        r = correr(sys.executable, os.path.join(SCRIPTS, "verificar_fidelidad.py"),
                   ORIGINAL, "no-existe.txt")
        self.assertEqual(r.returncode, 2)


class Unir(unittest.TestCase):
    def test_une_con_y_y_respeta_nombres(self):
        t = ("Goku entrena todos los días. La serie lo muestra sin prisa. "
             "Vegeta lo observa de lejos. Pero nunca lo admite.\n")
        conceptos = [("Goku", ["Goku"]), ("Vegeta", ["Vegeta"])]
        self.assertEqual(unir.unir(t, conceptos).strip(),
                         "Goku entrena todos los días y la serie lo muestra sin prisa "
                         "y Vegeta lo observa de lejos, pero nunca lo admite.")

    def test_avisa_nombres_que_no_estan_en_conceptos(self):
        dudosas = []
        r = unir.unir("Goku entrena. Vegeta lo observa.\n", dudosas=dudosas)
        self.assertIn("y vegeta", r)
        self.assertEqual(dudosas, ["Vegeta"])

    def test_no_cambia_ninguna_otra_palabra(self):
        texto = leer(ORIGINAL)
        r = unir.unir(texto, vf.cargar_conceptos(CONCEPTOS))
        fuera = ("y", "pero", "sin", "embargo", "asimismo", "además")
        palabras = lambda t: [w.lower() for w in re.findall(r"\w+", t) if w.lower() not in fuera]
        self.assertEqual(palabras(r), palabras(texto))
        self.assertLess(r.count(". "), texto.count(". "))

    def test_palabras_comunes_no_son_nombres_propios(self):
        conceptos = [("San Cristóbal de Las Casas", ["San Cristóbal de Las Casas"])]
        propios = unir.nombres_propios("Llegamos a San Cristóbal de Las Casas.", conceptos)
        self.assertIn("Cristóbal", propios)
        self.assertNotIn("Las", propios)

    def test_respeta_parrafos_y_titulos(self):
        r = unir.unir("Un título\n\nUno dos. Tres cuatro.\n\nCinco seis. Siete ocho.\n")
        self.assertEqual(r, "Un título\n\nUno dos y tres cuatro.\n\nCinco seis y siete ocho.\n")

    def test_el_ejemplo_final_es_reproducible(self):
        r = unir.unir(leer(HIP), vf.cargar_conceptos(CONCEPTOS))
        self.assertEqual(r, leer(FINAL))


class Hip(unittest.TestCase):
    def test_prompt_con_arranque_en_espanol(self):
        prompt, arranque = hip.construir_prompt("El turismo en la sierra crece.")
        self.assertEqual(arranque, "El turismo")
        self.assertTrue(prompt.startswith("<source_text>\n"))
        self.assertTrue(prompt.endswith("<target_text>\nEl turismo"))

    def test_limpia_la_salida(self):
        self.assertEqual(hip.limpiar_salida("El turismo", " de la sierra  crece.\n</target_text>basura"),
                         "El turismo de la sierra crece.")

    def test_reconoce_titulos(self):
        self.assertTrue(hip.es_titulo("Turismo y tecnología"))
        self.assertFalse(hip.es_titulo("El turismo crece."))

    def test_sin_modelo_avisa_y_sale_con_dos(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, HUMANIZAR_HIP_DIR=tmp)
            r = correr(sys.executable, os.path.join(SCRIPTS, "hip.py"), ORIGINAL,
                       "-o", os.path.join(tmp, "x.txt"), env=env)
            self.assertEqual(r.returncode, 2)
            self.assertIn("ERROR", r.stderr)


class Instalador(unittest.TestCase):
    def test_instala_y_desinstala(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = correr("bash", os.path.join(RAIZ, "install.sh"), "--destino", tmp)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            destino = os.path.join(tmp, "humanizar-es")
            for f in ("SKILL.md", "scripts/hip.py", "scripts/unir.py", "scripts/instalar_hip.sh"):
                self.assertTrue(os.path.isfile(os.path.join(destino, f)), f)
            self.assertFalse(os.path.exists(os.path.join(destino, "tests")))
            self.assertTrue(os.access(os.path.join(destino, "scripts", "instalar_hip.sh"), os.X_OK))
            correr("bash", os.path.join(RAIZ, "install.sh"), "--destino", tmp, "--desinstalar")
            self.assertFalse(os.path.exists(destino))

    def test_por_defecto_instala_para_todos_los_agentes(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, HOME=tmp)
            r = correr("bash", os.path.join(RAIZ, "install.sh"), env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            for carpeta in (".claude/skills", ".agents/skills"):
                self.assertTrue(os.path.isfile(os.path.join(tmp, carpeta, "humanizar-es", "SKILL.md")))
            correr("bash", os.path.join(RAIZ, "install.sh"), "--agente", "codex", env=env)
            self.assertTrue(os.path.isfile(os.path.join(tmp, ".codex/skills/humanizar-es/SKILL.md")))
            correr("bash", os.path.join(RAIZ, "install.sh"), "--desinstalar", env=env)
            self.assertFalse(os.path.exists(os.path.join(tmp, ".claude/skills/humanizar-es")))

    def test_frontmatter_cumple_el_formato_agent_skills(self):
        cabecera = leer(os.path.join(RAIZ, "SKILL.md")).split("---")[1]
        nombre = re.search(r"^name: (.+)$", cabecera, re.M).group(1).strip()
        descripcion = re.search(r"^description: (.+)$", cabecera, re.M).group(1).strip()
        self.assertEqual(nombre, "humanizar-es")
        self.assertLessEqual(len(descripcion), 1024)

    def test_instalador_del_modelo_tiene_hashes(self):
        s = leer(os.path.join(SCRIPTS, "instalar_hip.sh"))
        self.assertEqual(len(re.findall(r'_SHA="[0-9a-f]{64}"', s)), 2)


if __name__ == "__main__":
    unittest.main()
