# S-23 : levier pour un dernier tour ?

ft_a (lr 3e-5) égale le professeur au statique (14,12 s, 0 choc) mais n'améliore pas le banc (0,18 contre 0,16 choc/course). ft_b (lr 1e-4) dégrade le banc (0,48). Le temps statique semble plafonné à 14,12 s : le critère B strict (< 14,12 s) paraît hors d'atteinte par PPO + imitation.
Proposition pour l'unique itération supplémentaire : lr 3e-5, `--wall-penalty -100`, 3 M de pas (~16 min), deux graines. À valider par le lead.
