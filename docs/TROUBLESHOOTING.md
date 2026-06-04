# Troubleshooting

## Docker no responde

Ejecutar:

```powershell
docker info
```

Si Docker Desktop no esta iniciado, abrirlo y repetir `scripts\run-once.ps1`.

## `.env` faltante

Ejecutar:

```powershell
.\scripts\enroll-local.ps1 -TokenFile ..\legal-infrastructure\private\remote-processor-tokens.generated.txt
```

## El job queda `NEEDS_REVIEW`

Es esperado cuando falta texto vigente oficial. El procesador no debe inventar
comparaciones.

## El PDF no extrae texto

Quedara advertido como `PDF_TEXT_TOO_SHORT`. En una fase posterior se activa
OCR con Tesseract/OCRmyPDF y, opcionalmente, Ollama.

Para construir la imagen con Tesseract:

```powershell
docker build --build-arg INSTALL_OCR=true -t lexmapa-remote-processor:local .
```
