"""Tests with no network and no models. They run with the standard library:

    python3 -m unittest discover -s tests -v
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
EX_ES = os.path.join(ROOT, "examples", "es")
EX_EN = os.path.join(ROOT, "examples", "en")
ORIGINAL = os.path.join(EX_ES, "original.txt")
REWRITTEN = os.path.join(EX_ES, "1-rewritten.txt")
FINAL = os.path.join(EX_ES, "2-final.txt")
CONCEPTS = os.path.join(EX_ES, "concepts.txt")
ORIGINAL_EN = os.path.join(EX_EN, "original.txt")
REWRITTEN_EN = os.path.join(EX_EN, "1-rewritten.txt")
FINAL_EN = os.path.join(EX_EN, "2-final.txt")
CONCEPTS_EN = os.path.join(EX_EN, "concepts.txt")

sys.path.insert(0, SCRIPTS)
import check  # noqa: E402
import halves  # noqa: E402
import join  # noqa: E402
import rewrite  # noqa: E402


def run(*args, **kw):
    # The child writes UTF-8 too: on Windows it would write cp1252 and «» or ñ would break.
    kw["env"] = dict(kw.get("env") or os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          cwd=ROOT, **kw)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def script(name):
    return os.path.join(SCRIPTS, name)


class Check(unittest.TestCase):
    def test_example_keeps_every_concept(self):
        r = run(sys.executable, script("check.py"),
                ORIGINAL, REWRITTEN, FINAL, "--concepts", CONCEPTS)
        self.assertIn("1-rewritten.txt                27/27 = 100%", r.stdout)
        self.assertIn("2-final.txt                    27/27 = 100%", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_english_example_keeps_every_concept(self):
        r = run(sys.executable, script("check.py"),
                ORIGINAL_EN, REWRITTEN_EN, FINAL_EN, "--concepts", CONCEPTS_EN)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("LOST", r.stdout)

    def test_detects_lost_concept_and_flipped_negation(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad.txt")
            with open(bad, "w", encoding="utf-8") as fh:
                fh.write(read(ORIGINAL).replace("Heidegger", "un filósofo")
                         .replace("principio de no contradicción", "principio de contradicción"))
            r = run(sys.executable, script("check.py"),
                    ORIGINAL, bad, "--concepts", CONCEPTS)
            self.assertEqual(r.returncode, 1)
            self.assertIn("LOST", r.stdout)
            self.assertIn("«no contradiccion»", r.stdout)

    def test_negations_in_english(self):
        self.assertIn("not the", check.negations("This is not the answer."))
        self.assertIn("never again", check.negations("It will never again happen."))

    def test_ignores_accents_and_unicode_form(self):
        nfd_text = unicodedata.normalize("NFD", "La Crítica de la razón pura de Kant")
        self.assertTrue(check.pattern("critica de la razon pura").search(check.norm(nfd_text)))

    def test_whole_word_and_prefix(self):
        self.assertFalse(check.pattern("ser").search(check.norm("el servicio")))
        self.assertTrue(check.pattern("antinomia").search(check.norm("las antinomias")))
        self.assertTrue(check.pattern("subatómic*").search(check.norm("nivel subatómico")))

    def test_automatic_extraction(self):
        names = [n for n, _ in check.extract_concepts(read(ORIGINAL))]
        for expected in ("Aristóteles", "Tomás de Aquino", "Dasein"):
            self.assertIn(expected, names)
        self.assertNotIn("El", names)

    def test_list_flag_old_and_new(self):
        for flag in ("--list", "--listar"):
            r = run(sys.executable, script("check.py"), ORIGINAL, REWRITTEN, flag)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("concepts (automatic extraction)", r.stdout)

    def test_missing_file_exits_with_two(self):
        r = run(sys.executable, script("check.py"), ORIGINAL, "does-not-exist.txt")
        self.assertEqual(r.returncode, 2)


class Join(unittest.TestCase):
    def test_joins_with_y_and_respects_names(self):
        t = ("Goku entrena todos los días. La serie lo muestra sin prisa. "
             "Vegeta lo observa de lejos. Pero nunca lo admite.\n")
        concepts = [("Goku", ["Goku"]), ("Vegeta", ["Vegeta"])]
        self.assertEqual(join.join_text(t, concepts).strip(),
                         "Goku entrena todos los días y la serie lo muestra sin prisa "
                         "y Vegeta lo observa de lejos, pero nunca lo admite.")

    def test_flags_names_missing_from_concepts(self):
        doubtful = []
        r = join.join_text("Goku entrena. Vegeta lo observa.\n", doubtful=doubtful)
        self.assertIn("y vegeta", r)
        self.assertEqual(doubtful, ["Vegeta"])

    def test_changes_no_other_word(self):
        text = read(ORIGINAL)
        r = join.join_text(text, check.load_concepts(CONCEPTS))
        outside = ("y", "pero", "sin", "embargo", "asimismo", "además")
        words = lambda t: [w.lower() for w in re.findall(r"\w+", t) if w.lower() not in outside]  # noqa: E731
        self.assertEqual(words(r), words(text))
        self.assertLess(r.count(". "), text.count(". "))

    def test_common_words_are_not_proper_nouns(self):
        concepts = [("San Cristóbal de Las Casas", ["San Cristóbal de Las Casas"])]
        proper = join.proper_nouns("Llegamos a San Cristóbal de Las Casas.", concepts)
        self.assertIn("Cristóbal", proper)
        self.assertNotIn("Las", proper)

    def test_respects_paragraphs_and_titles(self):
        r = join.join_text("Un título\n\nUno dos. Tres cuatro.\n\nCinco seis. Siete ocho.\n")
        self.assertEqual(r, "Un título\n\nUno dos y tres cuatro.\n\nCinco seis y siete ocho.\n")

    def test_numbered_headings_stay_whole(self):
        # «1. Dimensión individual» came out as «1 y dimensión individual» (or «2; dimensión»).
        text = ("1. Dimensión individual: conocerme\n\n2.3. Método de trabajo\n\n"
                "Uno dos tres. Cuatro cinco seis.\n")
        for pauses in (None, 2):
            r = join.join_text(text, pauses=pauses, lang="es")
            self.assertIn("1. Dimensión individual: conocerme\n", r)
            self.assertIn("2.3. Método de trabajo\n", r)
        # a number closing a sentence still ends it
        self.assertEqual(join.join_text("Leí el capítulo 3. Luego descansé.\n", lang="es"),
                         "Leí el capítulo 3 y luego descansé.\n")

    def test_english_joins_with_and_and_respects_names(self):
        t = ("Dr. Smith moved to Boston. The city was cold. However, he stayed. "
             "I liked it. Moreover, the food was great. But winter came.\n")
        self.assertEqual(join.detect_language(t), "en")
        self.assertEqual(join.join_text(t).strip(),
                         "Dr. Smith moved to Boston and the city was cold, but he stayed "
                         "and I liked it and also the food was great, but winter came.")

    def test_pauses_leave_a_few_periods_and_keep_connectors(self):
        par = ("El ser es. El no-ser no es. Nada nace de la nada. Sin embargo, todo cambia. "
               "La semilla crece. El árbol da fruto. Segundo, el fuego calienta. El agua hierve.")
        out = join.join_text(par, pauses=2, lang="es")
        self.assertEqual(len(re.findall(r"\.(?:\s|$)", out)), 3, out)
        self.assertIn("Segundo, el fuego calienta", out)  # cut where the idea changes
        self.assertNotIn(" y sin embargo", out)
        self.assertNotIn(" y segundo", out)
        self.assertEqual(join.join_text(par, lang="es"), join.join_text(par, pauses=None, lang="es"))
        for p in join.join_text(par, pauses=2, lang="es").split(". "):
            self.assertGreater(len(re.findall(r"\w+", p)), 6, p)  # no sentence left alone

    def test_pauses_join_pero_without_a_double_connector(self):
        par = ("El ser es y no cambia nunca. El no-ser no es ni se piensa. Pero Heráclito "
               "dijo lo contrario. Todo fluye para él. Nada permanece igual. El río cambia.")
        for seed in (7, 11, 23):
            out = join.join_text(par, pauses=1, seed=seed, lang="es")
            self.assertNotIn("y pero", out)
            self.assertTrue(", pero Heráclito" in out or ". Pero Heráclito" in out, out)

    def test_detects_the_language(self):
        self.assertEqual(join.detect_language(read(ORIGINAL)), "es")
        self.assertEqual(join.detect_language(read(ORIGINAL_EN)), "en")
        self.assertEqual(join.detect_language("The cat sat on the mat and it was happy."), "en")

    def test_spanish_example_final_is_reproducible(self):
        r = join.join_text(read(REWRITTEN), check.load_concepts(CONCEPTS))
        self.assertEqual(r, read(FINAL))

    def test_english_example_final_is_reproducible(self):
        r = join.join_text(read(REWRITTEN_EN), check.load_concepts(CONCEPTS_EN))
        self.assertEqual(r, read(FINAL_EN))

    def test_cli_english_and_old_flags_give_the_same_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            new, old = os.path.join(tmp, "new.txt"), os.path.join(tmp, "old.txt")
            r1 = run(sys.executable, script("join.py"), REWRITTEN_EN, "-o", new,
                     "--concepts", CONCEPTS_EN, "--lang", "en", "--ratio", "1.0",
                     "--max-words", "400")
            r2 = run(sys.executable, script("join.py"), REWRITTEN_EN, "--salida", old,
                     "--conceptos", CONCEPTS_EN, "--idioma", "en", "--proporcion", "1.0",
                     "--maximo", "400")
            self.assertEqual(r1.returncode, 0, r1.stderr)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertEqual(read(new), read(FINAL_EN))
            self.assertEqual(read(old), read(FINAL_EN))


class Rewrite(unittest.TestCase):
    def test_prompt_with_spanish_lead(self):
        prompt, lead = rewrite.build_prompt("El turismo en la sierra crece.")
        self.assertEqual(lead, "El turismo")
        self.assertTrue(prompt.startswith("<source_text>\n"))
        self.assertTrue(prompt.endswith("<target_text>\nEl turismo"))

    def test_cleans_the_output(self):
        self.assertEqual(rewrite.clean_output("El turismo", " de la sierra  crece.\n</target_text>junk"),
                         "El turismo de la sierra crece.")

    def test_restores_the_percent_sign(self):
        self.assertEqual(rewrite.restore_percent_signs("Arabica es el 60% del total.",
                                                       "Arabica representa el 60 del total."),
                         "Arabica representa el 60% del total.")
        self.assertEqual(rewrite.restore_percent_signs("Sube 5% al año.", "Sube 5% cada año."),
                         "Sube 5% cada año.")
        self.assertEqual(rewrite.restore_percent_signs("Hay 60 países.", "Son 60 países."),
                         "Son 60 países.")

    def test_copied_share(self):
        p = ("Aristóteles sostiene que el acto tiene primacía sobre la potencia en varios "
             "sentidos y que la potencia de hablar se comprende cuando se ejerce el habla.")
        self.assertEqual(rewrite.copied_share(p, p), 1.0)
        half = ("Para Aristóteles el acto va antes que la potencia, y la potencia de hablar "
                "se comprende cuando se ejerce el habla.")
        self.assertLess(rewrite.copied_share(p, half), 0.6)
        # a shared name or phrase shorter than 8 words does not count as copied
        self.assertEqual(rewrite.copied_share("Parménides de Elea negó el cambio.",
                                              "Según Parménides de Elea, nada cambia."), 0.0)

    def test_retries_a_copied_try_and_names_the_lost_concept(self):
        """The fake llama copies the paragraph on the first try and rewrites it on the
        second; a paragraph that always loses «encina» stays as the original and the
        warning says which concept it lost."""
        text = ("Una bellota tiene la potencia de convertirse en una encina, pero una piedra "
                "no tiene esa potencia y nunca va a llegar a ser un árbol de ninguna clase.\n\n"
                "Cuando la encina adulta está en acto respecto de las capacidades que tenía cuando "
                "era bellota y por eso decimos que la potencia se ha actualizado del todo.\n")
        with tempfile.TemporaryDirectory() as tmp:
            for f in (rewrite.BASE, rewrite.ADAPTER):
                open(os.path.join(tmp, f), "w").close()
            fake = os.path.join(tmp, "fake_llama.py")
            calls = os.path.join(tmp, "calls")
            with open(fake, "w", encoding="utf-8") as fh:
                fh.write(
                    "import os, sys\n"
                    "args = sys.argv[1:]\n"
                    "prompt = open(args[args.index('-f') + 1], encoding='utf-8').read()\n"
                    "src = prompt.split('<source_text>\\n')[1].split('\\n</source_text>')[0]\n"
                    f"c = {calls!r}\n"
                    "n = int(open(c).read()) + 1 if os.path.exists(c) else 1\n"
                    "open(c, 'w').write(str(n))\n"
                    "if src.startswith('Cuando la'):\n"
                    "    out = ' planta se vuelve adulta, la potencia queda actualizada por completo'\n"
                    "    out += ' desde que era una bellota pequeña en el suelo del bosque.'\n"
                    "elif n == 1:\n"
                    "    out = ' ' + ' '.join(src.split()[2:])\n"
                    "else:\n"
                    "    out = (' puede llegar a ser encina; la piedra, en cambio, no tiene'\n"
                    "           ' esa potencia ni se hará árbol jamás, por más tiempo que pase.')\n"
                    "sys.stdout.buffer.write((out + '\\n</target_text>').encode('utf-8'))\n")
            src, out, conc = (os.path.join(tmp, n) for n in ("in.txt", "out.txt", "c.txt"))
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(text)
            with open(conc, "w", encoding="utf-8") as fh:
                fh.write("encina\nbellota\n")
            env = dict(os.environ, HUMANIZE_MODEL_DIR=tmp, HUMANIZE_LLAMA=fake)
            r = run(sys.executable, script("rewrite.py"), src, "-o", out, "--concepts", conc,
                    "--tries", "3", "--rescue", "0", "--threads", "1", env=env)
            # a paragraph left as the ORIGINAL is not a success: exit 3 and the command to redo it
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            self.assertIn("ACTION REQUIRED", r.stdout)
            self.assertIn("--only 2", r.stdout)
            first, second = read(out).strip().split("\n\n")
            self.assertTrue(first.startswith("Una bellota puede llegar a ser encina"), first)
            self.assertIn("Paragraph 1 of 2: done, try 2", r.stdout)
            self.assertEqual(second, text.strip().split("\n\n")[1])
            self.assertIn("2 (encina)", r.stdout)

    def test_keeps_the_least_copied_try_when_all_copy(self):
        text = ("Año tras año, el pingüino «Nuño» camina sin prisa hacia el sur por la costa "
                "helada, siempre por el mismo camino que conoce desde que era muy pequeño.\n")
        with tempfile.TemporaryDirectory() as tmp:
            fake = self._fake_llama(tmp)
            src, out = os.path.join(tmp, "in.txt"), os.path.join(tmp, "out.txt")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(text)
            env = dict(os.environ, HUMANIZE_MODEL_DIR=tmp, HUMANIZE_LLAMA=fake)
            r = run(sys.executable, script("rewrite.py"), src, "-o", out,
                    "--tries", "2", "--threads", "1", env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("copied long stretches", r.stdout)
            self.assertIn("1 (100%)", r.stdout)

    def test_only_redoes_the_listed_paragraphs_and_keeps_the_rest(self):
        text = ("Año tras año, el pingüino «Nuño» camina sin prisa hacia el sur.\n\n"
                "El mar helado cruje bajo sus patas cada mañana de invierno.\n")
        with tempfile.TemporaryDirectory() as tmp:
            fake = self._fake_llama(tmp)
            src, out = os.path.join(tmp, "in.txt"), os.path.join(tmp, "out.txt")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(text)
            with open(out, "w", encoding="utf-8") as fh:
                fh.write("Primero, ya corregido a mano.\n\nSegundo, ya corregido a mano.\n")
            env = dict(os.environ, HUMANIZE_MODEL_DIR=tmp, HUMANIZE_LLAMA=fake)
            r = run(sys.executable, script("rewrite.py"), src, "-o", out, "--only", "2",
                    "--tries", "1", "--threads", "1", env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            first, second = read(out).strip().split("\n\n")
            self.assertEqual(first, "Primero, ya corregido a mano.")
            self.assertEqual(second, text.strip().split("\n\n")[1])
            with open(out, "w", encoding="utf-8") as fh:
                fh.write("Solo un párrafo.\n")
            r = run(sys.executable, script("rewrite.py"), src, "-o", out, "--only", "2", env=env)
            self.assertEqual(r.returncode, 2)
            self.assertIn("same count", r.stderr)

    def test_rescue_rounds_rewrite_a_paragraph_that_first_runs_out_of_tries(self):
        """A paragraph whose first tries all lose a concept used to stay as the original
        (paragraph 4 of a real assignment). Now it gets extra rounds at a higher
        temperature, and the fake model only behaves from the third call on."""
        text = ("Una bellota tiene la potencia de convertirse en una encina, pero una piedra "
                "no tiene esa potencia y nunca va a llegar a ser un árbol de ninguna clase.\n")
        with tempfile.TemporaryDirectory() as tmp:
            for f in (rewrite.BASE, rewrite.ADAPTER):
                open(os.path.join(tmp, f), "w").close()
            fake, calls = os.path.join(tmp, "fake_llama.py"), os.path.join(tmp, "calls")
            with open(fake, "w", encoding="utf-8") as fh:
                fh.write(
                    "import os, sys\n"
                    f"c = {calls!r}\n"
                    "n = int(open(c).read()) + 1 if os.path.exists(c) else 1\n"
                    "open(c, 'w').write(str(n))\n"
                    "if n < 3:\n"
                    "    out = ' fruto del roble, y la piedra no se vuelve nada por mucho tiempo que pase.'\n"
                    "else:\n"
                    "    out = (' puede llegar a ser encina; la piedra, en cambio, no tiene'\n"
                    "           ' esa potencia ni se hará árbol jamás, por más tiempo que pase.')\n"
                    "sys.stdout.buffer.write((out + '\\n</target_text>').encode('utf-8'))\n")
            src, out, conc = (os.path.join(tmp, n) for n in ("in.txt", "out.txt", "c.txt"))
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(text)
            with open(conc, "w", encoding="utf-8") as fh:
                fh.write("encina\nbellota\n")
            env = dict(os.environ, HUMANIZE_MODEL_DIR=tmp, HUMANIZE_LLAMA=fake)
            # tries=1 and rescue=2: three calls in all; the third one is the good one
            r = run(sys.executable, script("rewrite.py"), src, "-o", out, "--concepts", conc,
                    "--tries", "1", "--rescue", "2", "--threads", "1", env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("round 2 at temperature 1.1", r.stdout)
            self.assertIn("done, rescue 2", r.stdout)
            self.assertNotEqual(read(out).strip(), text.strip())
            # canary: without the rescue rounds the same run leaves the original and exits 3
            os.remove(calls)
            r = run(sys.executable, script("rewrite.py"), src, "-o", out, "--concepts", conc,
                    "--tries", "1", "--rescue", "0", "--threads", "1", env=env)
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            self.assertEqual(read(out).strip(), text.strip())

    def test_a_heading_with_a_colon_is_a_title(self):
        for t in ("Introducción:", "A mis seres queridos:", "Conclusiones:"):
            self.assertTrue(rewrite.is_title(t), t)
        self.assertFalse(rewrite.is_title("Pbro. y Maestro: Felipe Ruiz Pérez."))
        self.assertFalse(rewrite.is_title("Estas son las razones por las cuales creo que es así, "
                                          "y las explico: primero, segundo, tercero y cuarto."))

    def test_vosotros_forms_are_rejected_only_when_the_original_has_none(self):
        o = "Cuando llegue la hora de mi muerte, acompáñame y confía en que la misericordia de la vida basta."
        for bad in ("Venid y dadme la fuerza de creer en la misericordia de la vida.",
                    "Os prometisteis la comunión con la vida de la muerte.",
                    "Si no coincidáis en la vida de la muerte, confía en la misericordia."):
            self.assertTrue(rewrite.vosotros_problem(o, bad), bad)
        self.assertIsNone(rewrite.vosotros_problem(o, "Cuando llegue la hora, confía en la misericordia."))
        self.assertIsNone(rewrite.vosotros_problem("Tenéis que venir, vuestra casa es la de la vida.",
                                                   "Tenéis que venir a la casa de la vida."))

    def test_an_accent_lost_in_a_short_name_is_rejected(self):
        o = "Los apuntes de Ruiz Pérez (2021) dicen que el decurso vital es la ruta de la vida."
        self.assertTrue(rewrite.proper_accent_problem(o, "Los apuntes de Ruiz Perez (2021) dicen otra cosa."))
        self.assertIsNone(rewrite.proper_accent_problem(o, "Según Ruiz Pérez (2021), la vida es una ruta."))
        self.assertIsNone(rewrite.proper_accent_problem("Tú sabes todo.", "Y tú lo sabes todo."))

    def test_check_reports_a_paragraph_that_is_still_the_original(self):
        o = ("Primer párrafo con muchas palabras distintas para que cuente como prosa y no como título, "
              "y que además sigue y sigue largo.\n\n"
              "Segundo párrafo también largo, con otras palabras bien distintas que tampoco son un título "
              "de ningún tipo en absoluto.\n")
        v = ("Primer párrafo con muchas palabras distintas para que cuente como prosa y no como título, "
             "y que además sigue y sigue largo.\n\n"
             "Otra versión del segundo bloque, dicha de manera diferente por completo y sin copiar nada.\n")
        self.assertEqual([n for n, _ in check.still_original(o, v)], [1])
        self.assertEqual(check.still_original(o, v + "\n\nextra"), None)
        with tempfile.TemporaryDirectory() as tmp:
            a, b, c = (os.path.join(tmp, n) for n in ("o.txt", "v.txt", "c.txt"))
            for path, text in ((a, o), (b, v), (c, "párrafo\n")):
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text)
            r = run(sys.executable, script("check.py"), a, b, "--concepts", c)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("still the ORIGINAL", r.stdout)
            self.assertIn("paragraph 1", r.stdout)
            # join.py refuses to join it, unless told to
            j = os.path.join(tmp, "j.txt")
            r = run(sys.executable, script("join.py"), b, "-o", j, "--original", a)
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertFalse(os.path.exists(j))
            self.assertIn("still the ORIGINAL", r.stderr)
            r = run(sys.executable, script("join.py"), b, "-o", j, "--original", a, "--allow-original")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_lead_replaces_the_opening_words(self):
        prompt, lead = rewrite.build_prompt("Uno de los problemas más importantes.", lead="Desde la")
        self.assertEqual(lead, "Desde la")
        self.assertTrue(prompt.endswith("<target_text>\nDesde la"))
        self.assertEqual(rewrite.build_prompt("Uno de los problemas.")[1], "Uno de")

    def test_citation_problem(self):
        o = ('Aristóteles: "aquello que está en potencia no puede actualizarse por sí mismo" '
             '(Física, III, 1). La bellota (el fruto de la encina).')
        ok = ('Escribe: "aquello que está en potencia no puede actualizarse por sí mismo" '
              '(Física, III, 1). La bellota (fruto de la encina).')
        self.assertIsNone(rewrite.citation_problem(o, ok))
        self.assertEqual(rewrite.citation_problem(o, ok.replace("aquello que", "la que")),
                         "(quote changed)")
        self.assertEqual(rewrite.citation_problem(o, ok.replace("(Física, III, 1)",
                                                                "(De Anima, libro i, cap. vi)")),
                         "(invented reference)")
        self.assertEqual(rewrite.citation_problem(
            "Mateo 9,36: la mirada compasiva de Jesús sobre las personas cansadas.",
            'Mateo 9,36: "¿Cuántos pastores hay entre vosotros?", dijo Jesús.'), "(invented quote)")
        self.assertIsNone(rewrite.citation_problem(
            "La frase siempre lo hemos hecho así muestra una mentalidad.",
            'La frase "siempre lo hemos hecho así" revela una mentalidad.'))

    def test_spelling_problem(self):
        o = ("La comunicación pastoral necesita oración y discernimiento; la composición "
             "de la comunidad y el Espíritu nos acompañan.")
        ok = ("La comunicación en la pastoral pide oración y discernimiento; el Espíritu y "
              "la composición de la comunidad nos acompañan.")
        self.assertIsNone(rewrite.spelling_problem(o, ok))
        for broken, why in (("comunicación", "comunicacion"), ("composición", "composicin"),
                            ("Espíritu", "Espiritu"), ("acompañan", "acompanan")):
            self.assertEqual(rewrite.spelling_problem(o, ok.replace(broken, why)),
                             f"(accents lost: {why.lower()})")
        self.assertEqual(rewrite.spelling_problem(o, ok.replace("oración", "oracio'n")),
                         "(broken accents)")
        self.assertIsNotNone(rewrite.spelling_problem(o, ok.replace("oración", "oraci n")
                                                      .replace("comunicación", "comunicaci n")
                                                      .replace("composición", "composici n")
                                                      .replace("Espíritu", "Esp ritu")))
        # a final accent dropped can leave a real word: «evaluará» -> «evaluar» is fine
        self.assertIsNone(rewrite.spelling_problem("El consejo evaluará el avance.",
                                                   "El consejo va a evaluar el avance."))
        self.assertIsNone(rewrite.spelling_problem("The council will review it.",
                                                   "The council's going to review it."))

    def test_language_problem(self):
        o = "VER significa escuchar y analizar la situación, sin culpar de inmediato a las personas."
        self.assertIsNone(rewrite.language_problem(
            o, "VER es escuchar la situación y analizarla antes de culpar a las personas."))
        self.assertEqual(rewrite.language_problem(
            o, "VER significa listening and understanding the situation before jumping to "
               "the conclusion that people are guilty."), "(switched to English)")
        self.assertEqual(rewrite.language_problem(
            o, "VER significa listening and understanding the situation, without blaming "
               "people immediately."), "(switched to English)")
        self.assertIsNone(rewrite.language_problem(
            "El equipo usa la plataforma en línea con su CRM.",
            "El equipo trabaja en la plataforma online con el CRM de la empresa."))
        self.assertEqual(rewrite.language_problem(
            "The council meets in the hall and decides the plan.",
            "El consejo se reúne en el salón y decide el plan de la parroquia."),
            "(switched to Spanish)")

    def test_negation_problem(self):
        o = "El criterio no sería solo el de la asistencia, sino la calidad de la escucha."
        self.assertIsNone(rewrite.negation_problem(
            o, "El criterio no se limitaría a la asistencia: contaría la calidad de la escucha."))
        self.assertIsNone(rewrite.negation_problem(
            o, "El criterio sería la asistencia y también, sobre todo, la escucha, no solo eso."))
        self.assertEqual(rewrite.negation_problem(
            o, "El criterio sería el de la asistencia, también de la escucha."), "(«no solo» lost)")
        self.assertEqual(rewrite.negation_problem(
            "El fruto no se medirá solo por la asistencia, sino por la comunión.",
            "No se medirá el fruto en términos de asistencia, sino de comunión."), "(«no solo» lost)")
        two = "No hay coro para competir ni grupos sin rumbo; nadie trabaja solo."
        self.assertEqual(rewrite.negation_problem(two, "Hay coro para competir y grupos con rumbo."),
                         "(negations lost: 4 -> 0)")
        # a single negation reworded is legitimate
        self.assertIsNone(rewrite.negation_problem("Son dones, no propiedades privadas.",
                                                   "Son dones en lugar de propiedades privadas."))
        self.assertIsNone(rewrite.negation_problem(
            "Que no solo sean destinatarios, sino también participantes.",
            "Que no sean simplemente destinatarios, sino que participen."))
        self.assertIsNone(rewrite.negation_problem(
            "Cada uno tendrá su tarea, pero no quedará un solo sector con la exclusividad.",
            "Cada uno tendrá su tarea, pero ningún sector se quedará con la exclusividad."))

    def test_repetition_problem(self):
        o = "Activismo sin orientación misionera: no hay un proceso para anunciar el Evangelio."
        bad = ("Activismo sin orientación misionera: no hay proceso para anunciar el Evangelio. "
               "2.- La parroquia es el lugar privilegiado para hacer proselitismo. "
               "3.- La parroquia es el lugar privilegiado para hacer proselitismo.")
        self.assertTrue(rewrite.repetition_problem(o, bad).startswith("(repeated:"))
        self.assertIsNone(rewrite.repetition_problem(o, bad.split(" 2.-")[0]))
        # the original's own repetition is allowed
        rep = ("Alejamiento de jóvenes y familias jóvenes; el alejamiento de jóvenes y familias "
               "jóvenes y el declive de la participación juvenil.")
        self.assertIsNone(rewrite.repetition_problem(rep, rep.replace("el declive", "la caída")))

    def _echo_llama(self, tmp):
        """A fake llama that writes back a different, faithful version each call."""
        for f in (rewrite.BASE, rewrite.ADAPTER):
            open(os.path.join(tmp, f), "w").close()
        fake = os.path.join(tmp, "echo_llama.py")
        calls = os.path.join(tmp, "calls")
        with open(fake, "w", encoding="utf-8") as fh:
            fh.write(
                "import os, sys\n"
                "args = sys.argv[1:]\n"
                "prompt = open(args[args.index('-f') + 1], encoding='utf-8').read()\n"
                "lead = prompt.split('<target_text>\\n')[1]\n"
                f"c = {calls!r}\n"
                "n = int(open(c).read()) + 1 if os.path.exists(c) else 1\n"
                "open(c, 'w').write(str(n))\n"
                "words = ['la semilla crece despacio', 'el árbol nace de la semilla',\n"
                "         'de la semilla sale un árbol']\n"
                "body = ' ' + words[n % 3] + ' y el lead fue ' + lead.replace(' ', '_') + ' en la vuelta ' + str(n) + ' del bosque.'\n"
                "sys.stdout.buffer.write((body + '\\n</target_text>').encode('utf-8'))\n")
        return fake

    def test_candidates_are_written_and_take_adopts_one(self):
        text = ("Uno de los problemas: la semilla se convierte en árbol con el tiempo y crece.\n\n"
                "La semilla crece y se vuelve un árbol grande con los años del bosque.\n")
        with tempfile.TemporaryDirectory() as tmp:
            fake = self._echo_llama(tmp)
            src, out = os.path.join(tmp, "in.txt"), os.path.join(tmp, "out.txt")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(text)
            with open(out, "w", encoding="utf-8") as fh:
                fh.write("Primero, ya corregido.\n\nSegundo, ya corregido.\n")
            env = dict(os.environ, HUMANIZE_MODEL_DIR=tmp, HUMANIZE_LLAMA=fake)
            r = run(sys.executable, script("rewrite.py"), src, "-o", out, "--only", "1",
                    "--candidates", "3", "--lead", "Desde la", "--threads", "1", env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            folder = out + ".candidates"
            files = sorted(os.listdir(folder))
            self.assertEqual(files, ["p01-1.txt", "p01-2.txt", "p01-3.txt"])
            first = read(os.path.join(folder, files[0]))
            self.assertTrue(first.startswith("Desde la "), first)
            self.assertIn("Desde_la", first)  # the lead reached the prompt
            self.assertEqual(read(out), "Primero, ya corregido.\n\nSegundo, ya corregido.\n")
            r = run(sys.executable, script("rewrite.py"), src, "-o", out,
                    "--take", "1=" + os.path.join(folder, files[1]), env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            new = read(out).split("\n\n")
            self.assertEqual(new[0], read(os.path.join(folder, files[1])).strip())
            self.assertEqual(new[1].strip(), "Segundo, ya corregido.")

    def test_take_adopts_several_paragraphs_at_once(self):
        # Several --take in one command used to keep only the last one, silently.
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.txt")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write("Uno viejo.\n\nDos viejo.\n\nTres viejo.\n")
            files = []
            for n in (1, 3):
                files.append(os.path.join(tmp, f"p{n}.txt"))
                with open(files[-1], "w", encoding="utf-8") as fh:
                    fh.write(f"Párrafo {n} nuevo.\n")
            r = run(sys.executable, script("rewrite.py"), ORIGINAL, "-o", out,
                    "--take", "1=" + files[0], "--take", "3=" + files[1])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(read(out), "Párrafo 1 nuevo.\n\nDos viejo.\n\nPárrafo 3 nuevo.\n")
            # one bad pair changes nothing
            r = run(sys.executable, script("rewrite.py"), ORIGINAL, "-o", out,
                    "--take", "2=" + files[0], "--take", "9=" + files[1])
            self.assertEqual(r.returncode, 2)
            self.assertIn("Dos viejo.", read(out))

    def test_candidates_need_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = self._echo_llama(tmp)
            env = dict(os.environ, HUMANIZE_MODEL_DIR=tmp, HUMANIZE_LLAMA=fake)
            r = run(sys.executable, script("rewrite.py"), ORIGINAL, "-o",
                    os.path.join(tmp, "x.txt"), "--candidates", "2", env=env)
            self.assertEqual(r.returncode, 2)
            self.assertIn("--only", r.stderr)

    def test_recognizes_titles(self):
        self.assertTrue(rewrite.is_title("Turismo y tecnología"))
        self.assertFalse(rewrite.is_title("El turismo crece."))

    def test_numbered_headings_with_a_period_are_titles(self):
        # «1. Dimensión individual: conocerme y orientar mi vida.» used to be rewritten.
        for t in ("1. Dimensión individual: conocerme y orientar mi vida.",
                  "2.3. Método de trabajo.", "2.- Fines de la parroquia.", "4) Cierre."):
            self.assertTrue(rewrite.is_title(t), t)
        for t in ("1. El ser es. El no-ser no es.",  # two sentences: a numbered paragraph
                  "3. La parroquia acompaña a las familias que llegan cada domingo desde lejos.",
                  "En 1990. Todo cambió."):
            self.assertFalse(rewrite.is_title(t), t)

    def _fake_llama(self, tmp):
        for f in (rewrite.BASE, rewrite.ADAPTER):
            open(os.path.join(tmp, f), "w").close()
        fake = os.path.join(tmp, "fake_llama.py")
        with open(fake, "w", encoding="utf-8") as fh:
            fh.write(
                "import sys\n"
                "args = sys.argv[1:]\n"
                "prompt = open(args[args.index('-f') + 1], encoding='utf-8').read()\n"
                "source = prompt.split('<source_text>\\n')[1].split('\\n</source_text>')[0]\n"
                "rest = ' '.join(source.split()[2:])\n"
                "sys.stdout.buffer.write((' ' + rest + '\\n</target_text>').encode('utf-8'))\n")
        return fake

    def test_runs_end_to_end_with_a_fake_llama(self):
        """The full path of rewrite.py without the model: prompt in a UTF-8 file, output
        read as UTF-8 (on Windows, without this, accents arrived broken) and file written.
        Uses the new env variables and English flags, then the old ones."""
        text = "Año tras año, el pingüino «Nuño» camina—sin prisa—hacia el sur.\n"
        with tempfile.TemporaryDirectory() as tmp:
            fake = self._fake_llama(tmp)
            src, out = os.path.join(tmp, "in.txt"), os.path.join(tmp, "out.txt")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(text)
            env = dict(os.environ, HUMANIZE_MODEL_DIR=tmp, HUMANIZE_LLAMA=fake)
            r = run(sys.executable, script("rewrite.py"), src, "-o", out,
                    "--tries", "1", "--threads", "1", env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(read(out), text)
            os.remove(out)
            env = {k: v for k, v in os.environ.items()
                   if k not in ("HUMANIZE_MODEL_DIR", "HUMANIZE_LLAMA")}
            env.update(HUMANIZAR_HIP_DIR=tmp, HUMANIZAR_LLAMA=fake)
            r = run(sys.executable, script("hip.py"), src, "--salida", out,
                    "--intentos", "1", "--hilos", "1", env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("hip.py is now rewrite.py", r.stderr)
            self.assertEqual(read(out), text)

    def test_without_model_warns_and_exits_with_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, HUMANIZE_MODEL_DIR=tmp)
            r = run(sys.executable, script("rewrite.py"), ORIGINAL,
                    "-o", os.path.join(tmp, "x.txt"), env=env)
            self.assertEqual(r.returncode, 2)
            self.assertIn("ERROR", r.stderr)


class Halves(unittest.TestCase):
    # A test essay was measured twice by mistake: the original pasted instead of the final
    # (53%), and the final with its accents broken by pbcopy («a√±os», 0%).
    BODY = ("Primera sección\n\n" + "Uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece. " * 30
            + "\n\nSegunda sección\n\n" + "Catorce quince dieciséis diecisiete dieciocho diecinueve veinte. " * 50
            + "\n")

    def test_cuts_before_the_heading_near_the_middle(self):
        a, b = halves.split_halves(self.BODY, max_words=100)
        self.assertTrue(b.startswith("Segunda sección\n\n"), b[:40])
        self.assertTrue(a.startswith("Primera sección"))
        self.assertEqual(halves.split_halves("Corto. Muy corto.\n"), ["Corto. Muy corto.\n"])

    def test_check_phrase_is_only_in_the_final_and_the_original_warns(self):
        original = "La experiencia es valiosa cuando me mantiene dispuesto a aprender y escuchar a otros."
        final = "La experiencia es un bien si me ayuda a estar abierto a la enseñanza y a escuchar."
        phrase = halves.check_phrase(final, original)
        self.assertIsNotNone(phrase)
        self.assertNotIn(" ".join(phrase.split()[:4]).lower(), original.lower())
        self.assertIsNone(halves.check_phrase(original, original))
        with tempfile.TemporaryDirectory() as tmp:
            o = os.path.join(tmp, "o.txt")
            with open(o, "w", encoding="utf-8") as fh:
                fh.write(original + "\n")
            r = run(sys.executable, script("halves.py"), o, "--original", o, "-o",
                    os.path.join(tmp, "x"))
            self.assertIn("WARNING", r.stdout)

    @unittest.skipIf(os.name == "nt", "fake clipboard tools are shell scripts")
    def test_copy_fails_when_the_clipboard_breaks_accents(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = os.path.join(tmp, "clip")
            for name, body in (("pbcopy", f"iconv -f macintosh -t utf-8 > '{store}'"),  # the bug
                               ("pbpaste", f"cat '{store}'")):
                path = os.path.join(tmp, name)
                with open(path, "w") as fh:
                    fh.write("#!/bin/sh\n" + body + "\n")
                os.chmod(path, 0o755)
            env = dict(os.environ, PATH=tmp + os.pathsep + os.environ["PATH"])
            text = os.path.join(tmp, "final.txt")
            with open(text, "w", encoding="utf-8") as fh:
                fh.write("Al llegar a los 61 años de edad considero que el crecimiento sigue.\n")
            r = run(sys.executable, script("halves.py"), text, "--original", text, "-o",
                    os.path.join(tmp, "x"), "--copy", "1", env=env)
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("accents", r.stderr)


class ModelDir(unittest.TestCase):
    def _put_model(self, directory):
        os.makedirs(directory, exist_ok=True)
        for f in rewrite.MODEL_FILES:
            open(os.path.join(directory, f), "w").close()

    def test_default_is_the_folder_every_version_used(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(rewrite.resolve_model_dir({}, home),
                             os.path.join(home, ".cache", "humanizar-es", "hip"))

    def test_env_variables_win_new_before_old(self):
        with tempfile.TemporaryDirectory() as home:
            self._put_model(os.path.join(home, ".cache", "humanizar-es", "hip"))
            self.assertEqual(rewrite.resolve_model_dir({"HUMANIZAR_HIP_DIR": "/old"}, home), "/old")
            self.assertEqual(rewrite.resolve_model_dir(
                {"HUMANIZAR_HIP_DIR": "/old", "HUMANIZE_MODEL_DIR": "/new"}, home), "/new")


class OldNames(unittest.TestCase):
    def test_unir_shim_matches_join(self):
        with tempfile.TemporaryDirectory() as tmp:
            new, old = os.path.join(tmp, "new.txt"), os.path.join(tmp, "old.txt")
            r1 = run(sys.executable, script("join.py"), REWRITTEN, "-o", new,
                     "--concepts", CONCEPTS)
            r2 = run(sys.executable, script("unir.py"), REWRITTEN, "-o", old,
                     "--conceptos", CONCEPTS)
            self.assertEqual(r1.returncode, 0, r1.stderr)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertIn("unir.py is now join.py", r2.stderr)
            self.assertEqual(read(old), read(new))
            self.assertEqual(read(old), read(FINAL))

    def test_verificar_fidelidad_shim_matches_check(self):
        args = (ORIGINAL, REWRITTEN, FINAL)
        r1 = run(sys.executable, script("check.py"), *args, "--concepts", CONCEPTS)
        r2 = run(sys.executable, script("verificar_fidelidad.py"), *args, "--conceptos", CONCEPTS)
        self.assertEqual(r2.returncode, r1.returncode)
        self.assertEqual(r2.stdout, r1.stdout)
        self.assertIn("verificar_fidelidad.py is now check.py", r2.stderr)

    def test_hip_and_instalar_hip_shims_reach_the_new_scripts(self):
        r = run(sys.executable, script("hip.py"), "--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--tries", r.stdout)
        # No llama.cpp (a path that does not exist): it stops before downloading anything.
        env = dict(os.environ, HUMANIZE_LLAMA=os.path.join(ROOT, "does-not-exist"))
        r = run(sys.executable, script("instalar_hip.py"), env=env)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("instalar_hip.py is now install_model.py", r.stderr)
        self.assertIn("llama.cpp is missing", r.stdout)

    def test_shims_can_still_be_imported(self):
        import unir
        import verificar_fidelidad
        self.assertIs(unir.join_text, join.join_text)
        self.assertIs(verificar_fidelidad.negations, check.negations)

    @unittest.skipUnless(shutil.which("bash") and os.name == "posix", "macOS and Linux shortcut")
    def test_instalar_hip_sh_shim_execs_install_model_sh(self):
        s = read(script("instalar_hip.sh"))
        self.assertIn("install_model.sh", s)
        r = run("bash", "-n", script("instalar_hip.sh"))
        self.assertEqual(r.returncode, 0, r.stderr)


INSTALL = (sys.executable, os.path.join(ROOT, "install.py"))


class Installer(unittest.TestCase):
    def test_installs_and_uninstalls(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(*INSTALL, "--dest", tmp)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            dest = os.path.join(tmp, "humanizar-es")
            for f in ("SKILL.md", "scripts/rewrite.py", "scripts/join.py", "scripts/check.py",
                      "scripts/install_model.py", "scripts/unir.py", "examples/en/2-final.txt"):
                self.assertTrue(os.path.isfile(os.path.join(dest, f)), f)
            self.assertFalse(os.path.exists(os.path.join(dest, "tests")))
            if os.name == "posix":
                self.assertTrue(os.access(os.path.join(dest, "scripts", "install_model.sh"), os.X_OK))
            run(*INSTALL, "--destino", tmp, "--desinstalar")
            self.assertFalse(os.path.exists(dest))

    def test_removes_an_install_under_the_old_test_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.path.join(tmp, "humanize-local")
            os.makedirs(os.path.join(old, "scripts"))
            with open(os.path.join(old, "SKILL.md"), "w") as fh:
                fh.write("---\nname: humanize-local\n---\n")
            r = run(*INSTALL, "--dest", tmp)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse(os.path.exists(old))
            self.assertIn("removed old version: " + old, r.stdout)
            self.assertTrue(os.path.isfile(os.path.join(tmp, "humanizar-es", "SKILL.md")))
            os.makedirs(old)  # uninstalling also cleans it up
            r = run(*INSTALL, "--dest", tmp, "--uninstall")
            self.assertFalse(os.path.exists(old))
            self.assertFalse(os.path.exists(os.path.join(tmp, "humanizar-es")))

    def test_by_default_installs_for_every_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, HOME=tmp)
            r = run(*INSTALL, env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            for folder in (".claude/skills", ".agents/skills"):
                self.assertTrue(os.path.isfile(os.path.join(tmp, folder, "humanizar-es", "SKILL.md")))
            run(*INSTALL, "--agent", "codex", env=env)
            self.assertTrue(os.path.isfile(os.path.join(tmp, ".codex/skills/humanizar-es/SKILL.md")))
            run(*INSTALL, "--agente", "dsh", env=env)
            self.assertTrue(os.path.isfile(os.path.join(tmp, ".dsh/skills/humanizar-es/SKILL.md")))
            run(*INSTALL, "--uninstall", env=env)
            self.assertFalse(os.path.exists(os.path.join(tmp, ".claude/skills/humanizar-es")))

    @unittest.skipUnless(shutil.which("bash") and os.name == "posix", "macOS and Linux shortcut")
    def test_the_bash_shortcut_calls_the_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("bash", os.path.join(ROOT, "install.sh"), "--dest", tmp)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(os.path.isfile(os.path.join(tmp, "humanizar-es", "SKILL.md")))

    def test_frontmatter_follows_the_agent_skills_format(self):
        header = read(os.path.join(ROOT, "SKILL.md")).split("---")[1]
        name = re.search(r"^name: (.+)$", header, re.M).group(1).strip()
        description = re.search(r"^description: (.+)$", header, re.M).group(1).strip()
        self.assertEqual(name, "humanizar-es")
        self.assertLessEqual(len(description), 1024)

    def test_model_installer_has_hashes(self):
        s = read(script("install_model.py"))
        self.assertEqual(len(re.findall(r'_SHA = "[0-9a-f]{64}"', s)), 2)


class Docx(unittest.TestCase):
    """docx_tools.py moves only the prose of a .docx and leaves the rest as it was."""

    PARAS = [
        "ESCUELA DIACONAL",
        "Introducción:",
        "   Este es el primer párrafo de la tarea, escrito con bastantes palabras para ser prosa.",
        "",
        "Desarrollo",
        "   Frase corta de enlace que aun así tiene más de doce palabras para contar como prosa.",
        "   Y este es el segundo párrafo, que sigue a la frase corta y tiene bastantes palabras también.",
        "Bibliografía",
        "Autor, A. (2021). Un libro que no se debe tocar [Apuntes] & más.",
    ]

    def _make(self, tmp):
        body = "".join(
            f'<w:p><w:pPr/><w:r><w:t xml:space="preserve">{t}</w:t></w:r></w:p>' if t
            else "<w:p/>" for t in self.PARAS)
        # one paragraph with its indent in a run of its own, as Word does
        body = body.replace(
            '<w:r><w:t xml:space="preserve">   Este es', '<w:r><w:t xml:space="preserve">   </w:t></w:r>'
            '<w:r><w:t xml:space="preserve">Este es')
        path = os.path.join(tmp, "t.docx")
        import zipfile
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("[Content_Types].xml", "<Types/>")
            z.writestr("word/document.xml", '<w:document xmlns:w="x"><w:body>' + body
                       + "</w:body></w:document>")
        return path

    def test_extract_and_build_round_trip(self):
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            docx = self._make(tmp)
            txt, mp, final, out = (os.path.join(tmp, n) for n in
                                   ("o.txt", "m.json", "f.txt", "out.docx"))
            r = run(sys.executable, script("docx_tools.py"), "extract", docx, "-o", txt, "--map", mp,
                    "--start", "Introducción:", "--stop", "Bibliografía", "--merge-short", "25")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            blocks = read(txt).strip().split("\n\n")
            self.assertEqual(len(blocks), 4)  # Introducción:, párrafo, Desarrollo, fusionado
            self.assertEqual(blocks[0], "Introducción:")
            self.assertTrue(blocks[3].startswith("Frase corta de enlace que aun así tiene más de doce palabras para contar como prosa. Y este es el segundo"))
            blocks[1] = "Texto nuevo del primer párrafo con \"comillas\" y & más <cosas> hasta ser prosa de verdad."
            blocks[3] = "Texto nuevo del segundo párrafo, ya fusionado con la frase corta, también largo."
            blocks[0] = "Cambiado"  # a title is never replaced, whatever the text says
            with open(final, "w", encoding="utf-8") as fh:
                fh.write("\n\n".join(blocks) + "\n")
            r = run(sys.executable, script("docx_tools.py"), "build", docx, "--map", mp,
                    "--text", final, "-o", out)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            xml = zipfile.ZipFile(out).read("word/document.xml").decode("utf-8")
            self.assertIn("Introducción:", xml)
            self.assertNotIn("Cambiado", xml)
            self.assertIn("ESCUELA DIACONAL", xml)
            self.assertIn("Un libro que no se debe tocar [Apuntes] & más.", xml)
            self.assertIn("comillas", xml)
            self.assertIn("&amp; más &lt;cosas&gt;", xml)  # escaped
            self.assertNotIn("Frase corta de enlace", xml)  # merged into the paragraph before
            self.assertNotIn("Y este es el segundo", xml)
            # the indent that sat in a run of its own is kept
            self.assertIn('<w:t xml:space="preserve">   Texto nuevo del primer', xml)
            # the output is still a document the extractor can read again
            r = run(sys.executable, script("docx_tools.py"), "extract", out, "-o", txt + "2",
                    "--map", mp + "2", "--start", "Introducción:", "--stop", "Bibliografía")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_build_refuses_a_text_with_another_number_of_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx = self._make(tmp)
            txt, mp, out = (os.path.join(tmp, n) for n in ("o.txt", "m.json", "out.docx"))
            run(sys.executable, script("docx_tools.py"), "extract", docx, "-o", txt, "--map", mp)
            with open(txt, "a", encoding="utf-8") as fh:
                fh.write("\nun bloque de más\n")
            r = run(sys.executable, script("docx_tools.py"), "build", docx, "--map", mp,
                    "--text", txt, "-o", out)
            self.assertEqual(r.returncode, 2)
            self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
