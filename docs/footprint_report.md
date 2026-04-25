# Footprint Report

## Current measured baseline

Measured with PowerShell on 24 April 2026:

- `tutor/`: `116469` bytes (`0.111 MB`)

## Live command to run before submission

On Linux or Colab:

```bash
du -sh tutor/
```

On PowerShell:

```powershell
$size=(Get-ChildItem tutor -Recurse -File | Measure-Object Length -Sum).Sum
$mb=[math]::Round($size/1MB,3)
"bytes=$size"
"mb=$mb"
```

## Per-component table

| Component | Size | Notes |
|---|---:|---|
| `tutor/` | 0.111 MB | Current Python package only |
| `assets/images/` | TODO | Add final visual scenes before submission |
| `assets/audio/` | TODO | TTS cache should stay excluded if allowed |
| local ASR checkpoint | TODO | Measure only if bundled |
| local LoRA adapter | TODO | Measure only if bundled |

## Notes

- Total app footprint must remain at or below 75 MB, excluding TTS cache.
- The current baseline is comfortably under the size limit because no heavy checkpoint is bundled yet.
