# Macchi-Älplermagronen-Alert

E-Mail-Bot, der werktags das Tagesmenü der Bäckerei [Macchi](https://www.macchi-baeckerei.ch/menu.html) prüft und nur dann eine Mail verschickt, wenn «Älplermagronen» auf dem Plan stehen.

## Ablauf

Die Action läuft nur auf GitHub und nutzt **keine Microsoft‑Dienste**. Sie ist zwei Mal pro Tag per Cron geplant, weil GitHub‑Zeit UTC ist:

```
0 5 * * 1-5  # entspricht 07:00 Sommerzeit (CEST)
0 6 * * 1-5  # entspricht 07:00 Winterzeit (CET)
```

Der Python-Skript sendet jedoch nur dann E-Mails, wenn die lokale Zeit in `Europe/Zurich` exakt 07:00 Uhr ist – so werden doppelte Mails vermieden und Zeitzonenwechsel automatisch abgedeckt.

## Benötigte Secrets

Legen Sie die folgenden Secrets im Repository an:

- `SMTP_HOST`
- `SMTP_PORT` (z.B. `587`)
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM` (optional, Standard = Username)
- `SMTP_TO` (Komma‑getrennte Empfänger)

Optionale Überschreibungen:

- `MENU_URL` (Standard: https://www.macchi-baeckerei.ch/menu.html)
- `KEYWORDS` (Komma‑getrennt; Standard: eingebauter Älplermagronen‑Mix)
- `KEYWORDS_REGEX` (optionales Regex‑Pattern, case‑insensitive)

## Manuell starten

Über **Actions → Macchi-Älplermagronen-Alert → Run workflow** lässt sich der Job auch per `workflow_dispatch` auslösen.
