# Vérification automatique de IABot_EURUSD
**19/19 scénarios réussis**

## ✅ 1. Référence EURUSD 2014-2017 : SL/TP/BE/trailing/risque/horaires conformes
_2265 trades, gain 53.9%, PF 1.19, DD 6.63%_
- OK  nombre de trades suffisant (2265)
- OK  chaque position a un SL et un TP dès l'ouverture
- OK  TP = 3 R (min 2.983 max 3.014, arrondi au point)
- OK  perte max par trade bornée (-1.03 R, gaps inclus)
- OK  risque par trade <= 0.4 % (+commission) : max 0.423 %
- OK  risque médian cohérent avec la cible (0.385 %, risque adaptatif inclus)
- OK  aucun échec d'ordre dans le journal
- OK  break-even à +0,1 R vérifié sur 349 déplacements (écarts : 0)
- OK  trailing désactivé par défaut : aucun déplacement de trailing
- OK  entrées uniquement dans la fenêtre 10h-13h (heure serveur)
- OK  toutes les positions fermées au plus tard à 15h le jour même
- OK  aucune entrée le vendredi après 18h
- OK  aucune position gardée le week-end quand le marché cote après 22h le vendredi (0 cas, tous des vendredis fériés/clôture anticipée : 0)
- OK  jamais plus de 3 position(s) simultanée(s) (max observé 3)
- OK  au moins 60 min entre deux entrées (min observé 0 days 01:00:00)
- OK  max 3 trade(s) par jour (max observé 3)

## ✅ 2. GBPUSD et EURJPY (autre paire, conversion de devise du profit) : risque correct, aucun plantage
- OK  GBPUSD : trades exécutés (584)
- OK  GBPUSD : risque 0.352 % (max 0.407 % ; lot minimum : max 0.407 %)
- OK  GBPUSD : SL et TP présents
- OK  EURJPY : trades exécutés (570)
- OK  EURJPY : risque 0.191 % (max 0.407 % ; lot minimum : max 0.407 %)
- OK  EURJPY : SL et TP présents

## ✅ 3. Courtier IOC uniquement / RETURN uniquement : mode de remplissage détecté
- OK  IOC : aucun ordre rejeté (0)
- OK  IOC : mêmes trades que la référence (578 vs 578)
- OK  RETURN : aucun ordre rejeté (0)
- OK  RETURN : mêmes trades que la référence (578 vs 578)

## ✅ 4. Requotes aléatoires (30 % des ordres) : nouvelles tentatives automatiques
- OK  requotes simulés (475)
- OK  trades quasi identiques (578 vs 578)
- OK  SL toujours posé malgré les requotes

## ✅ 5. Courtier qui ignore SL/TP à l'ouverture : l'EA les pose immédiatement
- OK  SL/TP posés après ouverture sur chaque trade (578/578)
- OK  toutes les positions finissent protégées

## ✅ 6. Courtier qui refuse SL et TP : fermeture de sécurité immédiate (jamais de position sans SL)
- OK  fermeture de sécurité déclenchée (1156 fois / 578 trades)
- OK  chaque position non protégée est fermée dans la même seconde

## ✅ 7. Stops level élevé (or 300 pts / Forex 100 pts) et freeze level : aucune requête invalide
- OK  le robot trade toujours (578)
- OK  aucun rejet 'invalid stops'
- OK  aucun rejet 'frozen'

## ✅ 8. Compte netting
- OK  netting : une seule position à la fois, comme l'impose ce type de compte (280 trades contre 578 en hedging)
- OK  mode netting détecté

## ✅ 9. Clôture partielle activée : une seule fois par position
- OK  clôtures partielles exécutées (217)
- OK  jamais deux clôtures partielles sur la même position

## ✅ 10. Limite de perte journalière (risque 4 %, limite 3 %) : arrêt pour la journée
- OK  limite journalière déclenchée (87 jour(s))
- OK  aucun nouveau trade le jour même après la limite

## ✅ 11. Coupe-circuit drawdown max (risque 3 %, limite 10 %) : arrêt définitif + fermeture
- OK  coupe-circuit déclenché
- OK  plus aucun trade après l'arrêt
- OK  positions fermées au déclenchement

## ✅ 12. Petit capital (300 USD) : jamais de risque supérieur à 2 % par trade
- OK  risque max 1.98 % <= 2 %
- OK  548 trades exécutés avec le lot minimum autorisé

## ✅ 13. Trading algorithmique désactivé : aucun ordre
- OK  aucune requête envoyée

## ✅ 14. Mode réel simulé + calendrier : pause autour des news à fort impact, panneau affiché
- OK  mode réel : le robot trade (578)
- OK  panneau d'information affiché
- OK  aucune entrée à +/-30 min des 15 news USD (0)
- OK  statut news

## ✅ 15. Session en heure GMT (testeur, décalage auto été/hiver US)
- OK  entrées entre 8h et 11h GMT (550 trades)

## ✅ 16. Paramètres invalides : initialisation refusée
- OK  INIT_PARAMETERS_INCORRECT renvoyé

## ✅ 17. Redémarrage du terminal en pleine position : reprise de la gestion (persistance)
- OK  une position est ouverte au moment de l'arrêt
- OK  la position #1735 est toujours gérée après redémarrage
- OK  résultat final identique à 1 % près (10163.90 vs 10163.90)

## ✅ 19. Risque adaptatif : réduction après une série négative, retour à la normale, mémoire persistante
- OK  bascule en mode réduit (44 fois) et retour à la normale (43 fois)
- OK  chaque entrée utilise le bon risque (2342 entrées conformes, 0 écarts)

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
- OK  EURUSD_ALL.csv : aucune erreur mémoire / UB / division par zéro (7860 trades)
- OK  EURUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (2265 trades)
- OK  EURUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (430 trades)
- OK  EURUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (243 trades)
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

