# Instalacion

## Windows

```powershell
.\scripts\setup.ps1
.\scripts\enroll-local.ps1 -TokenFile ..\legal-infrastructure\private\remote-processor-tokens.generated.txt
.\scripts\run.ps1
```

La ejecucion normal drena la cola: reclama y procesa jobs hasta que la API
responde que no hay pendientes, y entonces el contenedor termina.

`setup.ps1` valida primero hardware minimo. Si la PC no soporta tier 1, no
instala ni configura nada.

Para permitir instalacion automatica de Docker/Ollama:

```powershell
.\scripts\setup.ps1 -InstallDependencies -EnableOllama
```

La imagen Docker local usa este nombre:

```text
lexmapa/legal-remote-processor:local-ocr
```

OCR con Tesseract queda activado por defecto. Para reconstruir manualmente:

```powershell
.\scripts\build-image.ps1
```

Para ejecutar un solo job y salir:

```powershell
.\scripts\run.ps1 -Once
```

Para dejar un procesador permanente haciendo polling:

```powershell
.\scripts\run.ps1 -Continuous
```

`run.ps1` verifica si Docker esta levantado. Si Docker Desktop esta instalado
pero apagado, intenta iniciarlo, espera a que responda, revisa si la imagen
existe y la construye si falta.

## Linux

```bash
./scripts/setup.sh
cp .env.example .env
./scripts/run.sh
```

`run.sh` tambien drena la cola y termina cuando ya no hay pendientes.

En Linux el enrolamiento puede hacerse configurando `.env` manualmente con
`LEXMAPA_PROCESSOR_ID` y `LEXMAPA_PROCESSOR_SECRET`.

Para procesar un solo job:

```bash
./scripts/run.sh once
```

Para modo permanente:

```bash
./scripts/run.sh worker
```
