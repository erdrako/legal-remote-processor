# Local Smoke Test

Fecha: 2026-06-03

## Entorno

- Docker Desktop: disponible.
- Imagen local: `lexmapa-remote-processor:local`.
- OCR: Tesseract instalado dentro de la imagen con `INSTALL_OCR=true`.
- Ollama: no instalado; flujo ejecutado en modo deterministico.

## Validaciones

```powershell
python -m compileall src tests
python tests\test_parser.py
docker build --build-arg INSTALL_OCR=true -t lexmapa-remote-processor:local .
docker compose run --rm processor python -m processor.main doctor
docker compose run --rm processor python -m processor.main once
```

## Resultado API

Procesador enrolado:

```text
processor-06f4a879-c9ef-4468-86b7-50cda632b867
```

Jobs procesados:

| Job | Fuente | Estado | Resultado |
|---|---|---|---|
| `job-0a01cbd8-ac30-4530-883f-13009b722e1f` | Expediente CD-1/26 | `NEEDS_REVIEW` | PDF escaneado, 4 paginas, 0 caracteres extraidos antes de activar OCR |
| `job-edcd1ed5-dff5-4ba6-a2ad-fd8debd11c77` | Expediente S-361/26 | `NEEDS_REVIEW` | 11 paginas, 9674 caracteres, 5 artifacts, 2 provisions, 1 operation, 1 diff candidate |

Estado de cola posterior:

```text
PENDING = 5
NEEDS_REVIEW = 2
FAILED = 0
```

`NEEDS_REVIEW` es esperado: todavia falta resolver texto vigente oficial y
validacion legal antes de publicar diffs.
