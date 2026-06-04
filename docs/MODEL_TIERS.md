# Tiers de modelos

El procesador funciona sin IA en modo deterministico. Ollama es opcional para
mejorar OCR, referencias y candidatos en fases posteriores.

| Tier | Requisitos minimos | Modelo default | Uso |
|---|---|---|---|
| 1 | 8 GB RAM, 4 cores, 20 GB libres | `gemma3:270m` | clasificacion simple |
| 2 | 12 GB RAM, 4 cores, 30 GB libres | `gemma3:1b` | JSON estructurado |
| 3 | 16 GB RAM, 6 cores, 50 GB libres | `llama3.2:3b` | referencias y operaciones |
| 4 | 32 GB RAM o GPU 8 GB VRAM | `qwen2.5:7b` | documentos complejos |
| 5 | 64 GB RAM o GPU 16 GB VRAM | `qwen2.5:14b` | comparaciones extensas |

Regla: IA propone, codigo valida, fuente manda.
