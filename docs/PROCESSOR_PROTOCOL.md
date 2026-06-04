# Protocolo del procesador

## Enrolamiento

```http
POST /processors/enroll
Authorization: Bearer <PROCESSOR_ENROLLMENT_TOKEN>
```

Respuesta:

```json
{
  "processor": { "id": "processor-..." },
  "processorSecret": "..."
}
```

El secreto se guarda solo en `.env`.

## Heartbeat y jobs

Todas las llamadas posteriores usan:

```http
Authorization: Bearer <processorSecret>
x-processor-id: <processorId>
```

Flujo:

```text
POST /processors/heartbeat
POST /processors/jobs/claim
POST /processors/jobs/:id/progress
POST /processors/jobs/:id/result
```

## Estados terminales

- `COMPLETED`: resultado completo y validable.
- `NEEDS_REVIEW`: faltan fuentes, textos vigentes o revision humana.
- `NOT_COMPARABLE`: el documento no se puede comparar como diff legal.

## Resultado actual

El primer vertical slice devuelve `NEEDS_REVIEW` cuando procesa PDFs propuestos
sin texto vigente resuelto. Eso es correcto: no inventa el antes/despues.
