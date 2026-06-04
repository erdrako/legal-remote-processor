# Troubleshooting

## Docker no responde

Ejecutar:

```powershell
docker info
```

Si Docker Desktop no esta iniciado, abrirlo y repetir `scripts\run-once.ps1`.
El flujo recomendado es:

```powershell
.\scripts\run.ps1 -Once
```

Ese script intenta iniciar Docker Desktop automaticamente si esta instalado.
La ejecucion normal termina cuando no quedan pendientes en la cola. Si se uso
modo permanente por error, detenerlo con:

```powershell
docker compose rm --stop --force processor
```

## `.env` faltante

Ejecutar:

```powershell
.\scripts\enroll-local.ps1 -TokenFile ..\legal-infrastructure\private\remote-processor-tokens.generated.txt
```

## El job queda `NEEDS_REVIEW`

Es esperado cuando falta texto vigente oficial. El procesador no debe inventar
comparaciones.

## El PDF no extrae texto

Quedara advertido como `PDF_TEXT_TOO_SHORT` si el PDF no trae texto embebido y
OCR no esta disponible. La imagen local recomendada ya incluye OCR con
Tesseract.

Para construir la imagen con Tesseract:

```powershell
.\scripts\build-image.ps1
```
