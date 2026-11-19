# Vérification automatique de IABot_EURUSD v8
**19/19 scénarios réussis**

## ✅ 1. Référence EURUSD 2014-2017 : SL/TP/BE/trailing/risque/horaires conformes
_1750 trades, gain 79.8%, PF 1.52, DD 13.04%_
- OK  nombre de trades suffisant (1750)
- OK  chaque position a un SL et un TP dès l'ouverture
- OK  TP = 2 R (min 1.993 max 2.008, arrondi au point)
- OK  perte max par trade bornée (-1.43 R, gaps d'annonces inclus ; 5 trade(s) sous -1,15 R)
- OK  risque par trade <= 0.45 % (+commission) : max 0.469 %
- OK  risque médian cohérent avec la cible (0.429 %, risque adaptatif inclus)
- OK  aucun échec d'ordre dans le journal
- OK  break-even à +0,1 R vérifié sur 767 déplacements (écarts : 0)
- OK  trailing désactivé par défaut : aucun déplacement de trailing
- OK  entrées uniquement dans la fenêtre 8h-15h (heure serveur)
- OK  toutes les positions fermées au plus tard à 17h le jour même
- OK  aucune entrée le vendredi après 18h
- OK  aucune position gardée le week-end quand le marché cote après 22h le vendredi (0 cas, tous des vendredis fériés/clôture anticipée : 0)
- OK  jamais plus de 10 position(s) simultanée(s) (max observé 10)
- OK  au moins 15 min entre deux entrées (min observé 0 days 00:15:00)
- OK  max 10 trade(s) par jour (max observé 10)

## ✅ 2. GBPUSD et EURJPY : robot 100 % EURUSD, aucun trade sur une autre paire
- OK  GBPUSD : aucun ordre envoyé (0 trades)
- OK  GBPUSD : message clair dans le journal
- OK  EURJPY : aucun ordre envoyé (0 trades)
- OK  EURJPY : message clair dans le journal

## ✅ 3. Courtier IOC uniquement / RETURN uniquement : mode de remplissage détecté
- OK  IOC : aucun ordre rejeté (0)
- OK  IOC : mêmes trades que la référence (412 vs 412)
- OK  RETURN : aucun ordre rejeté (0)
- OK  RETURN : mêmes trades que la référence (412 vs 412)

## ✅ 4. Requotes aléatoires (30 % des ordres) : nouvelles tentatives automatiques
- OK  requotes simulés (311)
- OK  trades quasi identiques (411 vs 412)
- OK  SL toujours posé malgré les requotes

## ✅ 5. Courtier qui ignore SL/TP à l'ouverture : l'EA les pose immédiatement
- OK  SL/TP posés après ouverture sur chaque trade (412/412)
- OK  toutes les positions finissent protégées

## ✅ 6. Courtier qui refuse SL et TP : fermeture de sécurité immédiate (jamais de position sans SL)
- OK  fermeture de sécurité déclenchée (824 fois / 412 trades)
- OK  chaque position non protégée est fermée dans la même seconde

## ✅ 7. Stops level élevé (or 300 pts / Forex 100 pts) et freeze level : aucune requête invalide
- OK  le robot trade toujours (412)
- OK  aucun rejet 'invalid stops'
- OK  aucun rejet 'frozen'

## ✅ 8. Compte netting
- OK  netting : une seule position à la fois, comme l'impose ce type de compte (112 trades contre 412 en hedging)
- OK  mode netting détecté

## ✅ 9. Clôture partielle activée : une seule fois par position
- OK  clôtures partielles exécutées (143)
- OK  jamais deux clôtures partielles sur la même position

## ✅ 10. Limite de perte journalière (risque 4 %, limite 3 %) : arrêt pour la journée
- OK  limite journalière déclenchée (49 jour(s))
- OK  aucun nouveau trade le jour même après la limite

## ✅ 11. Coupe-circuit drawdown max (risque 3 %, limite 10 %) : arrêt définitif + fermeture
- OK  coupe-circuit déclenché
- OK  plus aucun trade après l'arrêt
- OK  positions fermées au déclenchement

## ✅ 12. Petit capital (300 USD) : jamais de risque supérieur à 2 % par trade
- OK  risque max 1.99 % <= 2 %
- OK  319 trades exécutés avec le lot minimum autorisé

## ✅ 13. Trading algorithmique désactivé : aucun ordre
- OK  aucune requête envoyée

## ✅ 14. Mode réel simulé + calendrier : pause autour des news à fort impact, panneau affiché
- OK  mode réel : le robot trade (412)
- OK  panneau d'information affiché
- OK  aucune entrée à +/-30 min des 15 news USD (0)
- OK  par défaut, une position gardée n'est pas fermée avant une news (option désactivée)
- OK  option activée : position gardée en perte fermée avant la news de 15 h 30 (70 fermeture(s) sur 20 jours testés, 0 après la news)

## ✅ 15. Session en heure GMT (testeur, décalage auto été/hiver US)
- OK  entrées entre 6h et 13h GMT (442 trades)

## ✅ 16. Paramètres invalides : initialisation refusée
- OK  INIT_PARAMETERS_INCORRECT renvoyé

## ✅ 17. Redémarrage du terminal en pleine position : reprise de la gestion (persistance)
- OK  position(s) ouverte(s) au moment de l'arrêt (2)
- OK  la position #1383 est toujours gérée après redémarrage
- OK  résultat final identique à 1 % près (10334.40 vs 10334.40)

## ✅ 19. Risque adaptatif : réduction après une série négative, retour à la normale, mémoire persistante
- OK  bascule en mode réduit (23 fois) et retour à la normale (23 fois)
- OK  chaque entrée utilise le bon risque (1788 entrées conformes, 0 écarts)

## ✅ 18. Exécution instrumentée (AddressSanitizer + UBSan + division par zéro) sur toutes les données
- OK  AUDUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  AUDUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  AUDUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURCAD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURCAD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURCHF_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURCHF_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURGBP_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURGBP_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURGBP_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURJPY_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURJPY_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURJPY_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURUSD_ALL.csv : aucune erreur mémoire / UB / division par zéro (5930 trades)
- OK  EURUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (1750 trades)
- OK  EURUSD_MT5c.csv : aucune erreur mémoire / UB / division par zéro (9085 trades)
- OK  EURUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (343 trades)
- OK  EURUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (196 trades)
- OK  GBPJPY_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  GBPJPY_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  GBPUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  GBPUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  GBPUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  NZDUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  NZDUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCAD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCAD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCAD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCHF_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCHF_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCHF_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDJPY_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDJPY_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDJPY_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  XAUUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  XAUUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  XAUUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)

