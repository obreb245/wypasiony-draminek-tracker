# Wypasiony Draminek Tracker

Narzędzie Python do monitorowania pozycji **wypasionydraminek.pl** i **draminek.pl** w:
- Wyszukiwarkach: Google PL (DataForSEO), Bing PL (Azure)
- Odpowiedziach AI: ChatGPT (OpenAI), Claude (Anthropic), Perplexity, Gemini

Dashboard dostępny pod: https://obreb245.github.io/wypasiony-draminek-tracker/

---

## Szybki start

```bash
# Klonowanie repo
git clone https://github.com/obreb245/wypasiony-draminek-tracker.git
cd wypasiony-draminek-tracker

# Instalacja zależności
pip install -r requirements.txt

# Konfiguracja kluczy API
cp .env.example .env
# Edytuj .env i uzupełnij klucze

# Testowy run bez kluczy API (mock mode)
python -m src.main run --mock
python -m src.main dashboard
```

---

## Konfiguracja kluczy API

### 1. DataForSEO (Google SERP)
- Konto: https://dataforseo.com/
- Po rejestracji: Dashboard → API Access → skopiuj login i hasło

### 2. Bing Web Search (Azure)
- Konto: https://portal.azure.com/
- Utwórz zasób: Cognitive Services → Bing Search v7
- Skopiuj klucz API

### 3. OpenAI (ChatGPT)
- Konto: https://platform.openai.com/
- API Keys → Create new secret key

### 4. Anthropic (Claude)
- Konto: https://console.anthropic.com/
- API Keys → Create Key

### 5. Perplexity
- Konto: https://www.perplexity.ai/settings/api
- Generate API key

### 6. Google AI (Gemini)
- Konto: https://aistudio.google.com/
- Get API key

---

## GitHub Secrets

Przejdź do: **Settings → Secrets and variables → Actions → New repository secret**

Dodaj następujące sekrety:
| Nazwa | Wartość |
|-------|---------|
| `DATAFORSEO_LOGIN` | Login z konta DataForSEO |
| `DATAFORSEO_PASSWORD` | Hasło z konta DataForSEO |
| `BING_API_KEY` | Klucz API z Azure |
| `OPENAI_API_KEY` | Klucz API z platform.openai.com |
| `ANTHROPIC_API_KEY` | Klucz API z console.anthropic.com |
| `PERPLEXITY_API_KEY` | Klucz API z perplexity.ai |
| `GEMINI_API_KEY` | Klucz API z aistudio.google.com |

---

## Włączenie GitHub Pages

1. Przejdź do: **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main`, folder: `/docs`
4. Zapisz → URL: `https://obreb245.github.io/wypasiony-draminek-tracker/`

---

## Uruchomienie runu

### Ręczne (GitHub Actions)
1. Przejdź do: **Actions → tracker → Run workflow**
2. Wybierz silniki (domyślnie: all) → Run workflow

### Automatyczne
Tracker uruchamia się automatycznie **1-go każdego miesiąca o 06:00 UTC**.

### Lokalne
```bash
# Mock run (bez kluczy API)
python -m src.main run --mock

# Tylko wybrane silniki
python -m src.main run --engines anthropic,openai --mock

# Dry run (bez zapisu do CSV)
python -m src.main run --mock --dry-run

# Generuj dashboard
python -m src.main dashboard

# Raport ostatniego runu
python -m src.main report --latest

# Porównaj z poprzednim runem
python -m src.main diff --since 2026-05-01
```

---

## Struktura danych

### data/master.csv
Główny plik z wynikami wszystkich runów (append-only):
```
run_date, run_id, engine, query_type, query_or_prompt, category, priority,
position, url_found, domain_matched, mention_text, response_excerpt,
raw_response_path, error, cost_pln
```

### data/runs/YYYY-MM-DD/
JSON dump każdego runu per silnik.

---

## Podpięcie subdomeny

Aby podpiąć `tracker.draminek.pl`:
1. W DNS draminek.pl dodaj rekord CNAME: `tracker` → `obreb245.github.io`
2. W repo: Settings → Pages → Custom domain → `tracker.draminek.pl`
