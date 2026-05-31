# ◈ AUTODIDACT v1.0

```
████████████████████████████████████████████████████
█  ◈ AUTODIDACT — SYSTÈME DE PARCOURS D'APPRENTISSAGE
█  Style terminal / Matrix — Pour autodidactes
████████████████████████████████████████████████████
```

## LANCEMENT

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python launch.py
# ou
python main.py
```

## FONCTIONNALITÉS

### ◈ Parcours d'apprentissage
- Créer des **parcours thématiques** (ML, Philosophie, Maths...)
- Ajouter une **description**, des **tags** et un **objectif**
- Suivre la progression globale avec une barre animée

### ◈ Types de ressources supportés
| Icône | Type | Source |
|-------|------|--------|
| `◈ WIKI` | Wikipedia | API officielle + contenu complet |
| `▶ VIDEO` | YouTube | Lecteur + transcript automatique |
| `◎ PDF` | Articles | ArXiv, articles académiques, web |
| `◉ BOOK` | Livres | Project Gutenberg, Wikisource, extraits |
| `◆ LINK` | Lien custom | N'importe quelle URL |

### ◈ Niveaux de difficulté
```
[1 INIT] █░░░░  — Débutant absolu
[2 BASE] ██░░░  — Bases acquises
[3 CORE] ███░░  — Niveau intermédiaire
[4 DEEP] ████░  — Avancé
[5 APEX] █████  — Expert
```

### ◈ Visionneur intégré
- **Wikipedia** : contenu complet via API (pas de pub, pas de distraction)
- **YouTube** : transcript automatique + lecteur intégré (avec `tkinterweb`)
- **ArXiv** : résumé et métadonnées des papiers scientifiques
- **Articles web** : extraction intelligente du texte principal
- **Gutenberg / Wikisource** : textes libres de droits

### ◈ Suivi
- Marquer les ressources comme **complétées** (✓)
- **Filtrer par niveau** pour suivre sa progression
- Barre de progression animée par parcours

## DÉPENDANCES

### Requises
- `python3-tk` — Interface graphique (sudo apt install python3-tk)
- `requests` — Requêtes HTTP
- `beautifulsoup4` + `lxml` — Extraction de contenu HTML
- `youtube-transcript-api` — Transcripts YouTube

### Optionnelles
- `tkinterweb` — Lecteur web intégré pour YouTube (`pip install tkinterweb`)

## RACCOURCIS CLAVIER

| Action | Description |
|--------|-------------|
| Double-clic sur un parcours | Éditer le parcours |
| Clic sur ✓/○ | Marquer comme fait |
| ▶ sur une carte | Ouvrir le contenu |

## DONNÉES

Les données sont stockées localement dans `autodidact.db` (SQLite).  
Aucune donnée n'est envoyée sur internet (sauf pour charger le contenu des ressources).
