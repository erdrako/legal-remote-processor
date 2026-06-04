# Instrucciones Para Codex

Este repositorio es el satelite `legal-remote-processor` de LexMapa.

## Alcance

- Mantener el procesador como componente externo por pull.
- No abrir puertos entrantes.
- No versionar tokens, credenciales, PDFs descargados ni `.env`.
- No publicar resultados como verdad legal aprobada.
- La IA local puede asistir, pero la fuente oficial y los validadores mandan.

## Flujo

1. El procesador se enrole contra `lexmapa-api`.
2. Envie heartbeats.
3. Tome jobs con lease.
4. Descargue documentos desde URL oficial.
5. Extraiga texto/OCR si corresponde.
6. Genere artifacts y candidatos de diff.
7. Devuelva resultados `COMPLETED`, `NEEDS_REVIEW` o `NOT_COMPARABLE`.

## Reglas

- Si falta fuente vigente, devolver `NEEDS_REVIEW`, no inventar comparaciones.
- Si el PDF no permite extraer texto y no hay OCR disponible, devolver
  `NEEDS_REVIEW` con warning.
- Si no hay fuente HTTP/HTTPS oficial, fallar o dejar `NEEDS_REVIEW`; no usar
  URLs inventadas.
- Mantener checks locales pasando antes de pushear.
