# Application de démonstration SQL Injection

Application web locale écrite en **Flask** et **SQLite** qui présente une petite
boutique de catalogue (produits, comptes, sessions, recherche, fiche produit et
administration) tout en comparant, pour chaque fonctionnalité, une
implémentation **volontairement vulnérable** à sa version **paramétrée et
sécurisée**. Elle sert exclusivement à l’apprentissage et à l’audit des risques
liés à l’injection SQL dans un environnement contrôlé.

> **Important :** cette application contient des failles de sécurité
> **intentionnelles**. Elle ne doit être exécutée que sur `127.0.0.1` et ne doit
> jamais être déployée sur un réseau, une adresse LAN ou Internet.

## Sommaire

- [Présentation](#présentation)
- [Fonctionnalités](#fonctionnalités)
- [Technologies](#technologies)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Lancement en développement](#lancement-en-développement)
- [Structure du projet](#structure-du-projet)
- [Scénarios d’utilisation](#scénarios-dutilisation)
- [Parcours de test de bout en bout](#parcours-de-test-de-bout-en-bout)
- [Tests automatisés](#tests-automatisés)
- [Sécurité](#sécurité)
- [Limites connues](#limites-connues)
- [Contribution](#contribution)

## Présentation

Ce dépôt fournit une application fonctionnelle : un catalogue de produits avec
comptes, rôles, session, espace utilisateur, recherche GET et POST, fiche
produit et zone d’administration. Chaque point d’entrée important correspond à
une requête HTTP rejouable (GET avec chaîne de requête, POST avec formulaire,
redirection, cookie de session, réponses d’erreur). Les routes vulnérables sont
systématiquement accompagnées d’une route de comparaison sécurisée (`*-safe`),
ce qui permet d’observer concrètement l’effet d’une entrée manipulée avant de
voir la correction appliquée.

Points d’entrée principaux :

| Domaine | Version vulnérable | Version sécurisée |
|---|---|---|
| Connexion POST | `POST /login` | `POST /login-safe` |
| Recherche GET | `GET /search?q=...` | `GET /search-safe?q=...` |
| Recherche POST | `POST /search-post` | — |
| Fiche produit | `GET /product?id=...` | `GET /product-safe?id=...` |
| Administration | `GET /admin-vulnerable?as_role=...` | `GET /admin` (contrôle serveur) |
| Santé / remise à zéro | `GET /health`, `scripts/init_db.py` | — |

## Fonctionnalités

- Catalogue de produits consultable (recherche texte GET et POST, fiche par identifiant).
- Comptes utilisateurs avec rôles (`user`, `analyst`, `admin`) et gestion de session.
- Espace utilisateur personnel après connexion.
- Zone d’administration réservée aux comptes administrateur.
- Comparaison systématique « route vulnérable » / « route sécurisée » sur chaque fonctionnalité sensible.
- Route de santé (`/health`) indiquant l’état de la base.
- Script d’initialisation et de remise à zéro de la base (`scripts/init_db.py`).
- Suite de tests automatisés (`pytest`).

## Technologies

- **Python 3.10+**
- **Flask 3.x** et **Werkzeug** (interface web et serveur de développement)
- **SQLite** (base intégrée à Python, aucune dépendance externe)
- **Jinja2** (templates HTML)
- **pytest** (tests automatisés)

Liste exacte des dépendances dans [`requirements.txt`](requirements.txt).

## Prérequis

- Windows 10 ou 11, ou tout système disposant d’un Python 3.10+ dans le terminal.
- Python 3.10 ou plus récent, avec l’option **Add Python to PATH** activée sous Windows.
- SQLite est inclus dans Python, aucun serveur de base de données séparé n’est requis.
- Aucun accès Internet n’est nécessaire pour exécuter l’application.

Vérifier l’installation de Python (PowerShell) :

```powershell
py --version
py -m pip --version
```

Si la commande `py` n’est pas disponible, utilisez `python` dans toutes les
commandes de ce document.

## Installation

Depuis un clone propre du dépôt (ou une archive décompressée dans un dossier
de travail), ouvrez un terminal dans le dossier racine puis :

1. Créer et activer un environnement virtuel :

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Si PowerShell bloque l’activation, autorisez uniquement la session courante :
`Set-ExecutionPolicy -Scope Process Bypass`, puis relancez l’activation.

2. Mettre à jour pip et installer les dépendances :

```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

3. Créer la base initiale (schéma + données de démonstration) :

```powershell
py scripts\init_db.py
```

Le script supprime l’ancienne base (`lab.db`), recrée le schéma et réinsère les
données. C’est aussi la procédure de remise à zéro.

## Configuration

Aucune variable d’environnement n’est requise. La clé de session Flask et le
chemin de la base sont définis dans [`app/app.py`](app/app.py) (clé fixe
destinée uniquement à un usage local). La base `lab.db` est générée à la racine
du dépôt par le script d’initialisation.

## Lancement en développement

Depuis le dossier racine, avec l’environnement virtuel activé :

```powershell
py -m flask --app app.app run --host 127.0.0.1 --port 5000
```

Puis ouvrez <http://127.0.0.1:5000/> dans un navigateur. Pour arrêter le
serveur, revenez dans le terminal et appuyez sur `Ctrl+C`.

Le démarrage explicite avec Flask est volontaire : il permet de placer un proxy
de débogage (par exemple l’outil « Burp Suite ») devant le serveur local afin
d’observer les requêtes échangées.

## Structure du projet
```
.
├── app
│   ├── __init__.py        Paquet application
│   └── app.py             Routes, base de données, session, sécurité
├── scripts
│   └── init_db.py         Création / remise à zéro de la base SQLite
├── static
│   └── style.css          Feuille de style (aucune dépendance externe)
├── templates
│   ├── base.html          Gabarit commun, navigation, flash
│   ├── index.html         Accueil
│   ├── login.html         Formulaire de connexion (vulnérable / sécurisé)
│   ├── dashboard.html     Espace utilisateur
│   ├── search.html        Recherche GET (vulnérable / sécurisé)
│   ├── search_post.html   Recherche POST
│   ├── product.html       Fiche produit
│   ├── admin.html         Page d’administration
│   └── denied.html        Accès refusé
├── tests
│   └── test_lab.py        Suite de tests pytest
├── requirements.txt       Dépendances Python
├── lab.db                 Base SQLite (générée par le script)
└── README.md              Ce document
```

## Scénarios d’utilisation

### Comptes de démonstration

Les comptes suivants sont créés par `scripts/init_db.py` :

| Utilisateur | Mot de passe | Rôle |
|---|---|---|
| `alice` | `alice123` | user |
| `bob` | `bob123` | user |
| `analyst` | `observe123` | analyst |
| `admin` | `admin123` | admin |

Les mots de passe en clair sont une simplification pédagogique propre à cette
application de démonstration ; ils ne doivent jamais être reproduits dans un
projet réel.

### Parcours proposé

1. **Découverte** : ouvrir l’accueil <http://127.0.0.1:5000/>, consulter la
   recherche `?q=network`, la fiche produit `?id=1`, puis le formulaire de
   connexion.
2. **Point d’entrée** : noter pour chaque fonctionnalité la méthode HTTP, le
   nom du paramètre et le format attendu.
3. **Saisies normale / malformée / manipulée** : rejouer une même requête avec
   une valeur standard, puis avec une apostrophe isolée, puis avec une
   condition logique, et comparer le code de statut, la longueur du contenu,
   le message renvoyé et les lignes affichées.
4. **Comparaison sécurisée** : rejouer les mêmes valeurs sur les routes
   `*-safe`, qui utilisent des requêtes paramétrées, et constater qu’aucune
   modification de la structure SQL ne se produit.
5. **Autorisation** : se connecter avec `alice`, constater le refus 403 sur
   `/admin`, comparer `/admin-vulnerable?as_role=admin` (décision contrôlée
   par le client), puis se connecter avec `admin` pour accéder à la version
   sûre de la page d’administration.

## Parcours de test de bout en bout

La démarche ci-dessous décrit la préparation, le lancement et la validation de
l’application de A à Z.

### 1. Préparer l’environnement

- Vérifier Python : `py --version`.
- Créer l’environnement virtuel : `py -m venv .venv` puis l’activer.
- Installer les dépendances : `py -m pip install -r requirements.txt`.

### 2. Initialiser les données

Exécuter `py scripts\init_db.py`. Le message de fin indique le chemin de
`lab.db` dans la racine du dépôt.

### 3. Lancer le serveur

```
py -m flask --app app.app run --host 127.0.0.1 --port 5000
```

### 4. Ouvrir l’application et réaliser les actions

- Ouvrir <http://127.0.0.1:5000/> : la page d’accueil s’affiche.
- Vérifier `GET /health` : il renvoie un JSON contenant `status: ok`,
  `database: true` et `schema_complete: true`.
- Rechercher `?q=network` : les produits Router Atlas et Switch Copper
  s’affichent.
- Ouvrir `?id=1` sur `/product` : la fiche Router Atlas s’affiche.
- Se connecter avec `alice / alice123` : redirection vers l’espace utilisateur
  qui affiche « Bonjour alice » et le catalogue.
- Se déconnecter, puis se connecter avec `admin / admin123` et ouvrir
  `/admin` : la page d’administration liste les utilisateurs.
- Tenter la recherche `q=%'` sur `/search-safe` : elle reste paramétrée et
  n’affiche aucune erreur de syntaxe SQL.

### 5. Résultats attendus

- Toutes les pages publiques répondent en HTTP 200.
- La connexion avec un compte valide redirige vers l’espace utilisateur.
- Un utilisateur non administrateur reçoit un refus 403 sur `/admin`.
- Les routes `*-safe` ne produisent jamais d’erreur de syntaxe SQL quelle que
  soit la valeur envoyée (les valeurs sont transmises comme paramètres).

### 6. Arrêter le serveur et valider

- Revenir dans le terminal du serveur et appuyer sur `Ctrl+C`.
- Relancer la suite de tests automatisés (section suivante).

### Commande de remise à zéro

Pour repartir d’un état propre dans un environnement de test :

1. Arrêter le serveur (`Ctrl+C`).
2. Exécuter `py scripts\init_db.py` (suppression du fichier `lab.db`,
   recréation du schéma et réinsertion des données).
3. Relancer le serveur.
4. Vérifier `GET /health`, puis relancer `py -m pytest -q`.
## Tests automatisés

Avec l’environnement virtuel activé, depuis la racine :

```powershell
py -m pytest -q
```

La suite vérifie le schéma et les données de la base, l’accessibilité des pages
publiques, les routes GET et POST, les connexions et sessions, les
redirections, les refus d’administration, l’autorisation vulnérable, les
messages d’erreur, la recherche POST et la non-injection sur les routes sûres.

Commandes d’inspection manuelle (serveur lancé) :

```powershell
curl.exe http://127.0.0.1:5000/health
curl.exe "http://127.0.0.1:5000/search?q=network"
curl.exe "http://127.0.0.1:5000/product?id=1"
curl.exe -X POST -d "username=alice&password=alice123" -i http://127.0.0.1:5000/login
```

Il n’existe pas de commande de lint, de formatage ou de contrôle de type
configurée dans ce dépôt.

## Sécurité

- **Ne déployez jamais cette application.** Les failles sont intentionnelles :
  concaténation SQL d’entrées utilisateur, mots de passe stockés en clair,
  décision d’autorisation contrôlée par le client et messages d’erreur
  détaillés reflétant l’exception SQLite.
- **Usage strictement local** : l’application ne doit être accessible que sur
  `127.0.0.1`.
- **Corrections de référence** : les versions sûres utilisent des requêtes
  paramétrées (placeholder `?` et tuple de paramètres), une autorisation
  déterminée côté serveur d’après la session et une gestion d’erreur qui ne
  divulgue pas le détail SQLite. Dans un projet réel, il faut en outre hacher
  les mots de passe, réduire les privilèges du compte SQLite, valider les
  formats et consigner les événements avec prudence.
- Ces expériences sont autorisées uniquement sur cette instance locale ; ne
  réutilisez aucune charge, aucun secret et aucune concaténation SQL dans une
  application réelle.

## Limites connues

- Authentification et autorisation volontairement inadéquates ; l’application
  n’est pas un modèle de gestion de secrets ou de sessions.
- Mots de passe stockés en clair dans la base (simplification pédagogique).
- Aucun mécanisme de protection de session autre que la clé Flask en dur.
- Les erreurs SQL brutes sont affichées sur les routes vulnérables pour
  illustrer le comportement réel d’une requête mal construite.

## Contribution

Ce dépôt est un support d’apprentissage. Toute contribution utile à la
documentation, aux tests ou à l’explication des scénarios est bienvenue.
Merci de vérifier que les modifications conservent la distinction
« vulnérable / sécurisée » et que `py -m pytest -q` réussit avant de proposer
une modification.