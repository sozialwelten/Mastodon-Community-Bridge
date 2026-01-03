# Mastodon-Community-Bridge

Findet thematische Verbindungen zwischen verschiedenen Mastodon-Instanzen und hilft dabei, interessante Accounts und Diskussionen über Instanz-Grenzen hinweg zu entdecken.

## Features

- 🔍 Analysiert öffentliche Timelines mehrerer Instanzen
- 🌉 Findet thematisch ähnliche Posts über Hashtags und Keywords
- 👥 Entdeckt interessante Accounts aus anderen Communities
- 📊 Zeigt Instanz-Statistiken und Top-Hashtags
- 💾 Exportiert Discovery Digests als JSON

## Installation

```bash
pip install requests
```

## Verwendung

```bash
# Zwei Instanzen vergleichen
python mastodon_bridge.py mastodon.social chaos.social

# Mit angepasster Ähnlichkeit (40%) und mehr Ergebnissen (15)
python mastodon_bridge.py mastodon.social fosstodon.org -s 0.4 -n 15

# Mit Statistiken und JSON-Export
python mastodon_bridge.py mastodon.social chaos.social --stats -o digest.json

# Mehrere Instanzen gleichzeitig
python mastodon_bridge.py mastodon.social chaos.social fosstodon.org techhub.social
```

## Optionen

```
positional arguments:
  instances             Mastodon-Instanzen (ohne https://)

options:
  -h, --help            Hilfe anzeigen
  -s, --min-similarity  Minimale Ähnlichkeit (0-1, Standard: 0.3)
  -n, --max-results     Max. Anzahl Ergebnisse (Standard: 10)
  --stats               Zeige Instanz-Statistiken
  -o, --output          Speichere Discovery Digest als JSON
```

## Beispiel-Output

```
🌉 Thematische Brücken gefunden!
================================================================================

🔗 Brücke #1 (Ähnlichkeit: 75%)
   Gemeinsame Tags: python, opensource

   📍 mastodon.social
   👤 @alice (Alice Developer)
   💬 Heute ein neues Python-Tool für #opensource Projekte veröffentlicht...
   🔗 https://mastodon.social/@alice/123456

   📍 chaos.social
   👤 @bob (Bob Hacker)
   💬 Suche nach guten #python #opensource Libraries für...
   🔗 https://chaos.social/@bob/789012
```

## Lizenz

GPL-3.0

## Autor

Michael Karbacher