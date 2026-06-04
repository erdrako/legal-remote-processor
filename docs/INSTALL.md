# Instalacion

## Windows

```powershell
.\scripts\bootstrap.ps1
.\scripts\enroll-local.ps1 -TokenFile ..\legal-infrastructure\private\remote-processor-tokens.generated.txt
.\scripts\run-once.ps1
```

`bootstrap.ps1` ejecuta primero el preflight. Si la PC no soporta tier 1, no
instala ni configura nada.

Para permitir instalacion automatica de Docker/Ollama:

```powershell
.\scripts\bootstrap.ps1 -InstallDependencies -EnableOllama
```

La imagen Docker no instala Tesseract por defecto. Para activar OCR:

```powershell
docker build --build-arg INSTALL_OCR=true -t lexmapa-remote-processor:local .
```

## Linux

```bash
./scripts/bootstrap.sh
cp .env.example .env
./scripts/run-once.sh
```

En Linux el enrolamiento puede hacerse configurando `.env` manualmente con
`LEXMAPA_PROCESSOR_ID` y `LEXMAPA_PROCESSOR_SECRET`.
