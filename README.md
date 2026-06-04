# LexMapa Remote Processor

Procesador remoto por Docker para LexMapa.

El procesador corre en una PC propia, se conecta por HTTPS saliente a la API de
LexMapa, reclama trabajos pendientes y devuelve resultados estructurados. No
abre puertos, no requiere IP fija y no publica datos directamente.

## Estado actual

Este primer vertical slice procesa jobs `GENERATE_DIFF_CANDIDATES` de Senado de
forma deterministica:

- descarga PDF desde fuente oficial;
- calcula hash del documento;
- extrae texto con PyMuPDF;
- segmenta articulos/provisiones por reglas;
- detecta referencias legales basicas;
- clasifica operaciones candidatas;
- devuelve artifacts y candidatos de diff en estado `NEEDS_REVIEW` cuando falta
  texto vigente.

Ollama queda soportado por configuracion, pero no es requerido para el primer
flujo deterministico. OCR con Tesseract queda activado por defecto en la imagen
local, porque varios PDFs oficiales son escaneados.

```powershell
docker build --build-arg INSTALL_OCR=true -t lexmapa/legal-remote-processor:local-ocr .
```

## Uso rapido

```powershell
.\scripts\setup.ps1
.\scripts\enroll-local.ps1 -TokenFile ..\legal-infrastructure\private\remote-processor-tokens.generated.txt
.\scripts\run.ps1
```

Para procesar un solo job y salir:

```powershell
.\scripts\run.ps1 -Once
```

Vista operativa:

```text
https://lexmapa.linqorait.com/ops
```

## Scripts

- `scripts/setup.ps1`: instalacion/setup inicial. Valida hardware minimo antes
  de configurar, crea `.env`, puede instalar Docker/Ollama con `winget`, inicia
  Docker Desktop si esta apagado y construye la imagen local.
- `scripts/run.ps1`: ejecucion normal. Verifica que Docker este levantado,
  intenta iniciarlo si no responde, construye la imagen si falta y arranca el
  procesador.
- `scripts/bootstrap.ps1`: wrapper de compatibilidad hacia `setup.ps1`.
- `scripts/build-image.ps1`: construye la imagen Docker
  `lexmapa/legal-remote-processor:local-ocr`.
- `scripts\enroll-local.ps1`: enrole local usando token privado externo.
- `scripts/run-once.ps1`: wrapper hacia `run.ps1 -Once`.
- `scripts/run-processor.ps1`: wrapper hacia `run.ps1`.
- `scripts/doctor.ps1`: diagnostico local.

Equivalentes `.sh` estan incluidos para Linux.

## Seguridad

No commitear:

- `.env`
- `.processor-state.json`
- `data/`
- `private/`
- PDFs descargados
- logs con tokens

Los secretos viven en Cloudflare y, para esta maquina, en archivos privados
fuera de git.

## Checks

```powershell
python -m compileall src tests
python tests\test_parser.py
```

## Smoke test

El primer despliegue local queda documentado en:

```text
docs/LOCAL_SMOKE_TEST.md
```
