# Controles humanos

Textos escritos por personas, sin intervención de IA, para calibrar los detectores.
Si un control sale marcado como IA, la corrida no sirve: el detector no está midiendo.

| Archivo | Qué es | Origen y licencia |
|---|---|---|
| `control-quijote.txt` | Inicio de *El ingenioso hidalgo don Quijote de la Mancha* (Cervantes, 1605): tasa, testimonio de erratas y comienzo de la dedicatoria | Dominio público |
| `control-wikipedia-metafisica-2014.txt` | Extracto del artículo «Metafísica» de Wikipedia en español, [revisión 79052614](https://es.wikipedia.org/w/index.php?oldid=79052614) del 28-dic-2014 | Autores: [colaboradores de Wikipedia](https://es.wikipedia.org/w/index.php?title=Metaf%C3%ADsica&action=history). Licencia [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/deed.es). Se quitó el marcado wiki; el texto no se modificó |

## Por qué estos dos

- **Wikipedia 2014** es el control que importa: prosa académica moderna, del mismo tema
  que el ensayo de ejemplo y anterior a los modelos de lenguaje actuales (2022).
- **El Quijote** solo sirve para comprobar que un instrumento distingue algo. Es
  español de 1605: comparar contra él mide arcaísmo, no humanidad.

## Conseguir tu propio control

Usa un texto que tú (o alguien de tu equipo) escribió antes de 2022 y que sea del mismo
registro que el que vas a humanizar. Si no tienes uno, una revisión antigua de
Wikipedia sirve:

```bash
curl -s "https://es.wikipedia.org/w/api.php?action=query&prop=revisions&titles=Metaf%C3%ADsica&rvlimit=1&rvprop=content|ids|timestamp&rvstart=2015-01-01T00:00:00Z&rvdir=older&format=json&formatversion=2"
```

Cambia `titles=` por el artículo que quieras y deja `rvstart` antes de 2022. Si
publicas el extracto, respeta la licencia CC BY-SA: cita la revisión y la licencia.
