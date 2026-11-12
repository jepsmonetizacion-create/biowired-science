# Biowired Science

Material de producción del canal de YouTube **Biowired Science** ([@BiowiredScience](https://www.youtube.com/@BiowiredScience)): la ciencia y la tecnología detrás de la salud diaria, en inglés.

## Contenido

| Carpeta | Qué hay |
| --- | --- |
| `branding/` | Logo y banner del canal (SVG y PNG) y el script que los genera |
| `videos/01-smartwatch-sleep/` | Guion, tiempos por frase, renderizador de las animaciones y descripción para YouTube del video 1 |
| `docs/` | Plan del canal y notas |

## Cómo regenerar el branding

Requiere Python 3, `rsvg-convert` (librsvg) y la fuente Inter.

```
python branding/make_branding.py
```

## Cómo renderizar el video 1

Requiere Python 3, `cairocffi`, `ffmpeg` y la fuente Inter. Coloca la narración como `videos/01-smartwatch-sleep/narration.mp3` (no se versiona).

```
cd videos/01-smartwatch-sleep
python render.py preview            # fotogramas de prueba en prev/
python render.py render salida.mp4  # video completo 1920x1080 a 30 fps
```

`timing.json` contiene el inicio y fin de cada frase de la narración; las escenas y los subtítulos se sincronizan con esos tiempos.

## Reglas de producción

- Cada dato del guion lleva su fuente en `description.txt`.
- Voz generada con IA y animaciones originales hechas con código; se declara en la descripción.
- Contenido educativo; no es consejo médico.
- Los archivos de audio y video no se suben al repositorio (ver `.gitignore`).
