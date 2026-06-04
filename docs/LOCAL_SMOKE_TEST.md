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
| `job-0a01cbd8-ac30-4530-883f-13009b722e1f` | Expediente CD-1/26 | `NEEDS_REVIEW` | OCR activo, 4 paginas, 5562 caracteres, 5 artifacts, 12 provisions, 7 operations, 7 diff candidates |
| `job-edcd1ed5-dff5-4ba6-a2ad-fd8debd11c77` | Expediente S-361/26 | `NEEDS_REVIEW` | 11 paginas, 9674 caracteres, 5 artifacts, 2 provisions, 1 operation, 1 diff candidate |

Estado de cola posterior:

```text
PENDING = 5
NEEDS_REVIEW = 2
FAILED = 0
```

`NEEDS_REVIEW` es esperado: todavia falta resolver texto vigente oficial y
validacion legal antes de publicar diffs.

## Reejecucion OCR Hojarasca

Fecha: 2026-06-03

Se reencolo manualmente `job-0a01cbd8-ac30-4530-883f-13009b722e1f`, se limpio
su salida parcial previa en D1 y se reproceso con la imagen Docker construida
con Tesseract.

Resultado verificado en D1:

```text
status = NEEDS_REVIEW
attempts = 1
completed_at = 2026-06-04T02:05:50.352Z
artifacts = 5
provisions = 12
operations = 7
affected_items = 6
diff_candidates = 7
char_count = 5562
page_count = 4
ocr_used = true
ocr_available = true
```

Durante la prueba se corrigio la generacion de IDs del procesador para que
provisions, operations, affected items y diff candidates queden prefijados por
`job_id`. Esto evita colisiones entre jobs cuando el backend persiste resultados
con `INSERT OR REPLACE`.

Tambien se ajusto la generacion de candidatos para no referenciar un
`affectedLegalItemId` inexistente. Si el item afectado todavia no fue persistido,
el candidato queda con ese vinculo en `null` y se conserva para revision.

Nota operativa: el job historico `job-edcd1ed5-dff5-4ba6-a2ad-fd8debd11c77`
quedo con artifacts pero sin filas estructuradas despues de limpiar las
colisiones de IDs anteriores. Reencolarlo con esta version del procesador
regenera su salida estructurada.
