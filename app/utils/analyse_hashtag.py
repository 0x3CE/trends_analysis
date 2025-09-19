# analyze_hashtags.py
"""
* **Rôle global** : Petit **script utilitaire autonome** qui fait une analyse rapide des hashtags sur une liste de tweets (sous forme de chaînes de caractères).
  👉 C’est une version simplifiée et indépendante de ce que `AnalyticsService` fait déjà avec la base.

* **Fonctionnalités** :

  1. **`extract_hashtags(tweets)`**

     * Parcourt une liste de textes de tweets.
     * Utilise une regex `#(\w+)` pour extraire les hashtags.
     * Retourne une **liste brute** de tous les hashtags trouvés (sans normalisation, sans tri).

  2. **`top_hashtags(tweets, n=10)`**

     * Appelle `extract_hashtags`.
     * Compte les occurrences avec `Counter`.
     * Retourne les `n` hashtags les plus fréquents sous forme de liste de tuples `(hashtag, count)`.

  3. **Exécution directe (`__main__`)**

     * Si on lance le script en ligne de commande :

       * Lit les tweets depuis `stdin`.
       * Affiche les `top_hashtags` au format :

         ```
         hashtag: count
         ```

* **Différence avec `AnalyticsService`** :

  * Ici, **pas de base de données** → ça marche juste sur des strings.
  * Pas de normalisation (hashtags gardent leur casse).
  * Pensé pour des petits tests ou de la CLI rapide, pas pour de la production API.

👉 Bref : c’est un **outil simple, à la Unix**, qui complète le service principal mais n’est pas intégré directement au workflow API (sauf via le petit endpoint `/tweets/top-hashtags`).

Tu veux que je continue avec les **`schemas`** ou les **`models`** après, pour attaquer le cœur de la structure data ?
"""
import re
from collections import Counter

def extract_hashtags(tweets):
    hashtags = []
    for tweet in tweets:
        found = re.findall(r'#(\w+)', tweet)
        hashtags.extend(found)
    return hashtags

def top_hashtags(tweets, n=10):
    hashtags = extract_hashtags(tweets)
    return Counter(hashtags).most_common(n)

if __name__ == "__main__":
    import sys
    tweets = sys.stdin.read().splitlines()
    for hashtag, count in top_hashtags(tweets):
        print(f"{hashtag}: {count}")
