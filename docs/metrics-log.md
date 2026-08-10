# Bitacora de metricas

Cada entrada se agrega al **cerrar una fase que corrio el arnes** (`eval/harness/run.py`). Nunca se afirma "mejoro" sin un numero antes/despues aqui.

Formato por entrada:

```markdown
## <fecha> — Fase N — <cambio aplicado>

| Metrica              | Antes | Despues |
|-----------------------|-------|---------|
| Precision (global)    |       |         |
| Recall (global)        |       |         |
| F1 (global)             |       |         |
| Over-redaction          |       |         |
| Latencia p50/p95/p99    |       |         |

**Que sorprendio:** <una nota honesta>
```

La primera entrada real llega en `TICKET-203` (baseline solo-regex).

---
