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

Ollama y OCR quedan soportados por configuracion, pero no son requeridos para el
primer flujo deterministico. La imagen Docker construye sin OCR por defecto para
evitar descargas de paquetes del sistema cuando no hacen falta:

```powershell
docker build --build-arg INSTALL_OCR=true -t lexmapa-remote-processor:local .
```

## Uso rapido

```powershell
.\scripts\bootstrap.ps1
.\scripts\enroll-local.ps1 -TokenFile ..\legal-infrastructure\private\remote-processor-tokens.generated.txt
.\scripts\build-image.ps1
.\scripts\run-once.ps1
```

Vista operativa:

```text
https://lexmapa.linqorait.com/ops
```

## Scripts

- `scripts/bootstrap.ps1`: preflight de hardware/sistema y build local.
- `scripts/build-image.ps1`: construye la imagen Docker.
- `scripts\enroll-local.ps1`: enrole local usando token privado externo.
- `scripts/run-once.ps1`: procesa un job y termina.
- `scripts/run-processor.ps1`: levanta el procesador continuo con Docker
  Compose.
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
