"""Pruebas de las herramientas sin dependencias. Corren con la biblioteca estandar:

    python3 -m unittest discover -s tests -v

Anclan los resultados del benchmark: si un cambio altera la fidelidad medida o el
medidor de estilo, estas pruebas lo dicen.
"""
import json
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
ORIGINAL = os.path.join(EJ, "00-original.txt")
ESTILO_01 = os.path.join(EJ, "01-reglas-estilo.txt")
CADENA_02 = os.path.join(EJ, "02-cadena-traduccion.txt")
ADVERS_03 = os.path.join(EJ, "03-adversarial.txt")
CONCEPTOS = os.path.join(EJ, "conceptos-metafisica.txt")

sys.path.insert(0, SCRIPTS)
import estilo  # noqa: E402
import verificar_fidelidad as vf  # noqa: E402


def correr(*args):
    return subprocess.run(args, capture_output=True, text=True, cwd=RAIZ)


class Fidelidad(unittest.TestCase):
    def test_reproduce_el_benchmark(self):
        r = correr(sys.executable, os.path.join(SCRIPTS, "verificar_fidelidad.py"),
                   ORIGINAL, ESTILO_01, CADENA_02, ADVERS_03, "--conceptos", CONCEPTOS)
        self.assertIn("01-reglas-estilo.txt           27/27 = 100%", r.stdout)
        self.assertIn("02-cadena-traduccion.txt       25/27 = 93%", r.stdout)
        self.assertIn("03-adversarial.txt             27/27 = 100%", r.stdout)
        self.assertEqual(r.returncode, 1, "una variante pierde conceptos: debe salir con 1")

    def test_variantes_fieles_salen_con_cero(self):
        r = correr(sys.executable, os.path.join(SCRIPTS, "verificar_fidelidad.py"),
                   ORIGINAL, ESTILO_01, ADVERS_03, "--conceptos", CONCEPTOS)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_detecta_la_negacion_invertida(self):
        r = correr(sys.executable, os.path.join(SCRIPTS, "verificar_fidelidad.py"),
                   ORIGINAL, CADENA_02, "--conceptos", CONCEPTOS)
        self.assertIn("«no contradiccion»", r.stdout)

    def test_ignora_acentos_y_forma_unicode(self):
        texto_nfd = unicodedata.normalize("NFD", "La Crítica de la razón pura de Kant")
        pat = vf.patron("critica de la razon pura")
        self.assertTrue(pat.search(vf.norm(texto_nfd)))

    def test_extraccion_automatica(self):
        with open(ORIGINAL, encoding="utf-8") as fh:
            nombres = [n for n, _ in vf.extraer_conceptos(fh.read())]
        for esperado in ("Aristóteles", "Tomás de Aquino", "Dasein", "res cogitans"):
            self.assertIn(esperado, nombres)
        self.assertNotIn("El", nombres)

    def test_palabra_completa_no_casa_con_otra_mas_larga(self):
        self.assertFalse(vf.patron("ser").search(vf.norm("el servicio")))
        self.assertTrue(vf.patron("antinomia").search(vf.norm("las antinomias")))
        self.assertTrue(vf.patron("subatómic*").search(vf.norm("nivel subatómico")))

    def test_negacion_entre_comillas(self):
        self.assertIn("no contradiccion", vf.negaciones("el principio de no «contradicción»"))

    def test_lista_que_no_corresponde_al_original_falla(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
            fh.write("Leibniz\n")
        try:
            r = correr(sys.executable, os.path.join(SCRIPTS, "verificar_fidelidad.py"),
                       ORIGINAL, ESTILO_01, "--conceptos", fh.name)
            self.assertEqual(r.returncode, 1)
        finally:
            os.unlink(fh.name)

    def test_archivo_inexistente_sale_con_dos(self):
        r = correr(sys.executable, os.path.join(SCRIPTS, "verificar_fidelidad.py"),
                   ORIGINAL, "no-existe.txt")
        self.assertEqual(r.returncode, 2)


class Estilo(unittest.TestCase):
    def medir(self, ruta):
        with open(ruta, encoding="utf-8") as fh:
            return estilo.medir(fh.read())

    def test_es_determinista(self):
        self.assertEqual(self.medir(ORIGINAL), self.medir(ORIGINAL))

    def test_ordena_como_el_benchmark(self):
        cv = {n: self.medir(p)["cv_longitud_oracion"]
              for n, p in [("00", ORIGINAL), ("01", ESTILO_01), ("02", CADENA_02), ("03", ADVERS_03)]}
        self.assertGreater(cv["01"], cv["00"])
        self.assertGreater(cv["03"], cv["00"])
        self.assertLessEqual(cv["02"], cv["00"] + 0.01)

    def test_encuentra_delatores(self):
        m = estilo.medir("Cabe destacar que la IA no solo es útil, sino también rápida. "
                         "En la actualidad, constituye un avance.")
        etiquetas = {d["delator"] for d in m["delatores"]}
        self.assertIn("cabe destacar / señalar / mencionar", etiquetas)
        self.assertIn("no solo ... sino", etiquetas)
        self.assertIn("en la actualidad / hoy en día", etiquetas)
        self.assertIn("constituye / se erige como", etiquetas)

    def test_delatores_en_plural_y_pasado(self):
        m = estilo.medir("Juegan un papel clave. Resultan indispensables. Representó un hito.")
        self.assertEqual(m["delatores_total"], 3)

    def test_sin_falsos_positivos_conocidos(self):
        m = estilo.medir("La asamblea constituyente votó. ¿Por qué no solo él? Sino todos.")
        self.assertEqual(m["delatores_total"], 0)

    def test_abreviaturas_no_parten_oraciones(self):
        self.assertEqual(len(estilo.oraciones("Nació en el siglo I a. C. en Rodas. Lo vio el Dr. Pérez.")), 2)

    def test_tramo_uniforme(self):
        self.assertEqual(estilo.tramo_uniforme([30, 20, 20, 20]), 3)
        self.assertEqual(estilo.tramo_uniforme([5, 40, 6, 35]), 1)

    def test_parrafos_con_lineas_cortadas(self):
        self.assertEqual(len(estilo.parrafos("linea uno\nlinea dos\n\notro parrafo")), 2)

    def test_texto_limpio_sin_delatores(self):
        self.assertEqual(estilo.medir("Salí temprano. Llovía.")["delatores_total"], 0)

    def test_salida_json(self):
        r = correr(sys.executable, os.path.join(SCRIPTS, "estilo.py"), ORIGINAL, "--json")
        self.assertEqual(r.returncode, 0)
        self.assertIn(ORIGINAL, json.loads(r.stdout))


class Cubo(unittest.TestCase):
    """Las piezas del cubo que no necesitan red ni modelos."""

    @classmethod
    def setUpClass(cls):
        import cubo
        cls.cubo = cubo
        cls.conceptos = vf.cargar_conceptos(CONCEPTOS)

    def test_lee_json_y_rescata_respuestas_cortadas(self):
        ev = self.cubo.extraer_variantes
        self.assertEqual(ev('{"v": ["uno dos", "tres cuatro"]}'), ["uno dos", "tres cuatro"])
        self.assertEqual(ev('{"v": ["Primera completa.", "Segunda cort'), ["Primera completa."])
        self.assertEqual(ev("<think>...</think> sin json"), [])

    def test_rechaza_concepto_perdido(self):
        o = "Aristóteles defendió el principio de no contradicción en su obra."
        c = "Aristóteles defendió el principio de contradicción en su obra."
        self.assertIn(self.cubo.motivo_rechazo(o, c, self.conceptos), ("concepto", "negacion"))

    def test_rechaza_negacion_perdida(self):
        o = "No podemos conocer las cosas en sí tal como son."
        c = "Podemos conocer las cosas en sí tal como son."
        self.assertEqual(self.cubo.motivo_rechazo(o, c, self.conceptos), "negacion")

    def test_rechaza_delator_nuevo(self):
        o = "La metafísica es la pregunta más radical sobre la realidad."
        c = "La metafísica constituye la pregunta más radical sobre la realidad."
        self.assertEqual(self.cubo.motivo_rechazo(o, c, self.conceptos), "delator")

    def test_acepta_giro_fiel(self):
        o = "La física estudiaba las entidades sujetas al cambio empírico."
        c = "La física se ocupaba de las entidades sometidas al cambio empírico."
        self.assertIsNone(self.cubo.motivo_rechazo(o, c, self.conceptos))

    def test_palabras_repetidas(self):
        with open(ORIGINAL, encoding="utf-8") as fh:
            self.assertEqual(self.cubo.palabras_repetidas(fh.read(), self.conceptos), ["metafísica"])

    def test_partir_y_unir_conserva_el_texto(self):
        with open(ORIGINAL, encoding="utf-8") as fh:
            texto = fh.read()
        partes = self.cubo.partir(texto)
        self.assertTrue(partes[0]["titulo"])
        self.assertEqual(" ".join(self.cubo.unir(partes).split()), " ".join(texto.split()))

    def test_bucle_completo_con_piezas_falsas(self):
        """El cubo de punta a punta, sin red ni modelos: un detector falso que premia
        lo corto y un generador que propone quitar 'muy'. El titulo no se toca, el
        revisor veta un giro y el resto se conserva."""

        class Detector:
            def puntuar(self, texto):
                return {"total": float(len(texto))}

        class Generador:
            modelos = ["falso"]

            def variantes(self, oracion, *a, **k):
                return [oracion.replace("muy ", "")]

            def revisar(self, pares):
                return {i for i, (o, n) in enumerate(pares) if "vetada" in o}

        texto = ("Titulo del texto\n\nLa idea era muy clara. El tema era muy amplio.\n\n"
                 "Esta frase vetada era muy larga.\n")
        with tempfile.TemporaryDirectory() as tmp:
            salida = os.path.join(tmp, "s.txt")
            res, ini, fin, st = self.cubo.por_parrafo(
                texto, Generador(), Detector(), [], "academico", 2, 1, 1, salida)
            self.assertTrue(os.path.exists(salida))
        self.assertTrue(res.startswith("Titulo del texto"))
        self.assertIn("La idea era clara. El tema era amplio.", res)
        self.assertIn("Esta frase vetada era muy larga.", res)
        self.assertLess(fin, ini)
        self.assertEqual(st["aceptadas"], 2)

    def test_clave_desde_variable_o_archivo(self):
        viejo = os.environ.pop("HUMANIZAR_API_KEY", None)
        archivo_viejo = self.cubo.ARCHIVO_CLAVE
        try:
            with tempfile.TemporaryDirectory() as tmp:
                self.cubo.ARCHIVO_CLAVE = os.path.join(tmp, "api_key")
                self.assertEqual(self.cubo.leer_clave(), "")
                with open(self.cubo.ARCHIVO_CLAVE, "w") as fh:
                    fh.write("desde-archivo\n")
                self.assertEqual(self.cubo.leer_clave(), "desde-archivo")
                os.environ["HUMANIZAR_API_KEY"] = "desde-variable"
                self.assertEqual(self.cubo.leer_clave(), "desde-variable")
        finally:
            self.cubo.ARCHIVO_CLAVE = archivo_viejo
            os.environ.pop("HUMANIZAR_API_KEY", None)
            if viejo is not None:
                os.environ["HUMANIZAR_API_KEY"] = viejo

    def test_revisor_vacio_parte_el_lote(self):
        """Si el revisor contesta vacio con el lote entero, se reintenta por mitades y
        solo se rechaza lo que de verdad rechaza (antes se vetaba el lote completo)."""
        gen = object.__new__(self.cubo.Generador)
        gen.revisor, gen.revisor_fallos = "falso", 0

        def llamar(modelo, prompt, temperatura):
            if prompt.count("Par ") > 1:
                return ""
            return '{"rechazar": [0]}' if "MALA" in prompt else '{"rechazar": []}'
        gen._llamar = llamar
        pares = [("a b", "c d"), ("e f", "MALA g"), ("h i", "j k"), ("l m", "n o")]
        self.assertEqual(gen.revisar(pares), {1})
        self.assertEqual(gen.revisor_fallos, 0)

    def test_rechaza_asterisco_copiado(self):
        o = "Una lluvia fuerte puede provocar un derrumbe en la carretera."
        c = "Un aguacero puede causar un derrumbe* en la carretera."
        self.assertEqual(self.cubo.motivo_rechazo(o, c, []), "simbolo")

    def test_correlacion_de_rangos(self):
        import calibrar
        self.assertAlmostEqual(calibrar.spearman([1, 2, 3], [10, 20, 30]), 1.0)
        self.assertAlmostEqual(calibrar.spearman([1, 2, 3], [30, 20, 10]), -1.0)


class Ruleta(unittest.TestCase):
    """Las piezas de la ruleta que no necesitan red ni modelos."""

    @classmethod
    def setUpClass(cls):
        import ruleta
        cls.r = ruleta

    def test_lee_sinonimos_y_descarta_indices_raros(self):
        d = self.r.leer_sinonimos('{"1": ["analizaba", "examinaba"], "2": [], "9": ["x"]}', 3)
        self.assertEqual(d, {1: ["analizaba", "examinaba"], 2: []})
        self.assertEqual(self.r.leer_sinonimos("sin json", 3), {})

    def test_reemplazo_conserva_la_mayuscula(self):
        self.assertEqual(self.r.reemplazar("Estudia el horizonte.", 0, 7, "examina"), "Examina el horizonte.")
        self.assertEqual(self.r.reemplazar("Se estudia el todo.", 3, 10, "examina"), "Se examina el todo.")

    def test_encuentra_la_oracion_de_una_palabra(self):
        p = "La física estudiaba el cambio. La filosofía primera buscaba lo permanente."
        self.assertEqual(self.r.oracion_de(p, p.find("buscaba")),
                         "La filosofía primera buscaba lo permanente.")

    def test_no_toca_conceptos_protegidos(self):
        protegidas = self.r.palabras_protegidas(vf.cargar_conceptos(CONCEPTOS))
        self.assertIn("contingencia", protegidas)
        self.assertIn("subatomic", protegidas)


class Orquestador(unittest.TestCase):
    def test_medir_rapido_propaga_fallo_de_fidelidad(self):
        r = correr("bash", os.path.join(SCRIPTS, "medir.sh"), ORIGINAL, CADENA_02,
                   "--conceptos", CONCEPTOS, "--rapido")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_medir_rapido_ok(self):
        r = correr("bash", os.path.join(SCRIPTS, "medir.sh"), ORIGINAL, ESTILO_01,
                   "--conceptos", CONCEPTOS, "--rapido")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ESTILO", r.stdout)


class Instalador(unittest.TestCase):
    def test_instala_y_desinstala(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = correr("bash", os.path.join(RAIZ, "install.sh"), "--destino", tmp)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            destino = os.path.join(tmp, "humanizar-es")
            self.assertTrue(os.path.isfile(os.path.join(destino, "SKILL.md")))
            self.assertFalse(os.path.exists(os.path.join(destino, "tests")))
            self.assertTrue(os.access(os.path.join(destino, "scripts", "estilo.py"), os.X_OK))
            r = correr("bash", os.path.join(RAIZ, "install.sh"), "--destino", tmp, "--desinstalar")
            self.assertFalse(os.path.exists(destino))

    def test_por_defecto_instala_para_todos_los_agentes(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, HOME=tmp)
            r = subprocess.run(["bash", os.path.join(RAIZ, "install.sh")],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            for carpeta in (".claude/skills", ".agents/skills"):
                self.assertTrue(os.path.isfile(os.path.join(tmp, carpeta, "humanizar-es", "SKILL.md")))
            r = subprocess.run(["bash", os.path.join(RAIZ, "install.sh"), "--agente", "codex"],
                               capture_output=True, text=True, env=env)
            self.assertTrue(os.path.isfile(os.path.join(tmp, ".codex/skills/humanizar-es/SKILL.md")))
            subprocess.run(["bash", os.path.join(RAIZ, "install.sh"), "--desinstalar"],
                           capture_output=True, text=True, env=env)
            self.assertFalse(os.path.exists(os.path.join(tmp, ".claude/skills/humanizar-es")))
            self.assertFalse(os.path.exists(os.path.join(tmp, ".agents/skills/humanizar-es")))

    def test_frontmatter_cumple_el_formato_agent_skills(self):
        with open(os.path.join(RAIZ, "SKILL.md"), encoding="utf-8") as fh:
            cabecera = fh.read().split("---")[1]
        nombre = re.search(r"^name: (.+)$", cabecera, re.M).group(1).strip()
        descripcion = re.search(r"^description: (.+)$", cabecera, re.M).group(1).strip()
        self.assertEqual(nombre, "humanizar-es")
        self.assertRegex(nombre, r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertLessEqual(len(descripcion), 1024)

    def test_destino_que_ya_termina_en_el_nombre_no_anida(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = os.path.join(tmp, "humanizar-es")
            r = correr("bash", os.path.join(RAIZ, "install.sh"), "--destino", destino)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(os.path.isfile(os.path.join(destino, "SKILL.md")))
            self.assertFalse(os.path.exists(os.path.join(destino, "humanizar-es")))


class Ensuciar(unittest.TestCase):
    """El paso que mete imperfecciones de redaccion, sin modelos."""

    @classmethod
    def setUpClass(cls):
        import ensuciar
        cls.e = ensuciar
        cls.conceptos = vf.cargar_conceptos(CONCEPTOS)
        cls.texto = open(os.path.join(EJ, "00-original.txt"), encoding="utf-8").read()

    def test_reproducible(self):
        a = self.e.ensuciar(self.texto, "extra", self.conceptos, semilla=3)
        b = self.e.ensuciar(self.texto, "extra", self.conceptos, semilla=3)
        self.assertEqual(a, b)
        self.assertNotEqual(a, self.e.ensuciar(self.texto, "extra", self.conceptos, semilla=4))

    def test_por_defecto_no_toca_la_ortografia(self):
        sucio = self.e.ensuciar(self.texto, "extra", self.conceptos)
        palabras = lambda t: [w.lower() for w in re.findall(r"\w+", t)]
        # mismas palabras, mismos acentos: solo cambian comas, puntos y espacios
        self.assertEqual(palabras(sucio), palabras(self.texto))
        self.assertNotEqual(sucio, self.texto)

    def test_ortografia_opcional_sin_tocar_conceptos(self):
        sucio = self.e.ensuciar(self.texto, "extra", self.conceptos, ortografia=True)
        self.assertNotEqual(re.findall(r"\w+", sucio.lower()), re.findall(r"\w+", self.texto.lower()))
        t, s = vf.norm(self.texto), vf.norm(sucio)
        for nombre, variantes in self.conceptos:
            if any(vf.patron(v).search(t) for v in variantes):
                self.assertTrue(any(vf.patron(v).search(s) for v in variantes), nombre)

    def test_nivel_mas_alto_toca_mas(self):
        import difflib
        parecido = lambda n: difflib.SequenceMatcher(None, self.texto, self.e.ensuciar(self.texto, n)).ratio()
        self.assertGreater(parecido("ligero"), parecido("extra"))


class Hip(unittest.TestCase):
    """Las piezas de hip.py que no necesitan el modelo."""

    def test_prompt_con_arranque_en_espanol(self):
        import hip
        prompt, arranque = hip.construir_prompt("El turismo en la sierra crece.")
        self.assertEqual(arranque, "El turismo")
        self.assertTrue(prompt.startswith("<source_text>\n"))
        self.assertTrue(prompt.endswith("<target_text>\nEl turismo"))

    def test_limpia_la_salida(self):
        import hip
        self.assertEqual(hip.limpiar_salida("El turismo", " de la sierra  crece.\n</target_text>basura"),
                         "El turismo de la sierra crece.")

    def test_reconoce_titulos(self):
        import hip
        self.assertTrue(hip.es_titulo("Turismo y tecnología"))
        self.assertFalse(hip.es_titulo("El turismo crece."))


if __name__ == "__main__":
    unittest.main()
