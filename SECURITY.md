# Seguridad

## Secretos

El repositorio no debe contener:

- tokens de enrolamiento;
- secretos de procesador;
- archivos `.env`;
- PDFs descargados;
- resultados locales con datos operativos sensibles.

## Comunicacion

El procesador solo usa HTTPS saliente hacia la API de LexMapa. No requiere
abrir puertos ni exponer servicios locales.

## Resultados

Los resultados del procesador son candidatos operativos. No equivalen a dato
legal aprobado ni asesoramiento legal.

Si falta evidencia, fuente vigente o texto verificable, el job debe quedar como
`NEEDS_REVIEW` o `NOT_COMPARABLE`.
