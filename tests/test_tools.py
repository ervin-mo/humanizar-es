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
                    "--tries", "3", "--threads", "1", env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
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

    def test_recognizes_titles(self):
        self.assertTrue(rewrite.is_title("Turismo y tecnología"))
        self.assertFalse(rewrite.is_title("El turismo crece."))

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


if __name__ == "__main__":
    unittest.main()
