# Fruit Parameters Reference

## Parameter Classification Table

| Parameter | Group | Reason |
|-----------|-------|--------|
| Tref_C | #1 | Reference storage temperature typically matches the published optimal storage temperature for the commodity (e.g., Kader's tables). |
| RH_ref | #1 | Optimal/typical storage RH is a standard published value in postharvest storage guides. |
| firmeza_0_default | #1 | Harvest-time firmness is routinely measured with a penetrometer and reported in variety/postharvest studies. |
| brix_0_default | #1 | Harvest-time Brix (refractometer reading) is one of the most commonly published maturity indices. |
| acidez_0_default | #1 | Harvest-time titratable acidity is a standard, widely reported maturity index. |
| brix_max | #1 | Typical peak Brix at full ripeness is a genuine reported ceiling for most cultivars (variety descriptions, ripening studies). |
| qual_firm_threshold | #1 | Minimum "acceptable" firmness for retail/consumer quality is often defined in marketing/grading standards. |
| qual_brix_target | #1 | Target/minimum Brix for consumer acceptance is sometimes explicitly set in marketing standards (e.g. EU minimum-maturity rules). |
| qual_acidez_target | #1 | A "balanced flavor" acid target (or Brix:acid ratio) is a recognized sensory-quality benchmark in postharvest literature. |
| SL_ref | #1 | Typical/maximum storage life under recommended conditions is a standard published figure. |
| T_critical_high_C | #1 | Heat-damage thresholds are specifically documented in postharvest physiology literature. |
| T_critical_low_C | #1 | Chilling-injury thresholds are specifically documented per commodity/cultivar in postharvest literature. |
| RH_mold_thr | #1 | RH thresholds above which decay risk rises sharply are documented in postharvest pathology literature (e.g. Botrytis risk above ~95% RH). |
| Ea_J | #2 | Activation energy for softening is rarely published directly; usually only a Q10 value is available, requiring conversion/derivation. |
| k_firm_ref | #2 | Softening rate constant "at Tref" is specific to this model's assumed decay form — papers report firmness-vs-time curves, not this coefficient. |
| beta_RH | #2 | Invented sensitivity coefficient linking RH deficit to softening rate in this specific formula; no external standard equivalent. |
| firmeza_min | #2 | Mathematical asymptote of the decay curve, not a value papers report — end-of-storage firmness data can inform it, but it's a fitting choice. |
| brix_min | #2 | Functions as the logistic curve's lower floor, essentially redundant with brix_0_default — a modeling artifact, not a biologically meaningful minimum. |
| brix_g | #2 | Logistic growth-rate constant specific to this model's curve shape; not a quantity reported in postharvest studies. |
| acidez_min | #2 | Floor of the acid-decay curve; like firmeza_min, informed by but not equal to any single published "minimum acid" figure. |
| k_acidez_ref | #2 | Acid-degradation rate constant specific to this model's math; no standard published equivalent. |
| Ea_acidez_J | #2 | Activation energy for acid loss is rarely published directly. |
| T_critical_high_rate | #2 | Currently zeroed out/commented in your data — an unset damage-accrual rate with no literature equivalent yet. |
| T_critical_low_rate | #2 | Same as above — placeholder damage-accrual rate, model-internal. |
| mold_rate_ref | #2 | Base mold growth rate specific to this kinetic form; postharvest pathology papers report incidence (%) under given RH/T, not a rate constant like this. |
| mold_sens_RH | #2 | Sensitivity coefficient for RH excess in the mold model; invented for this formula. |
| mold_max_penalty | #2 | An arbitrary scaling factor on the 0–100 quality index — a modeling choice, not a measured quantity. |
| Ea_mold_J | #2 | Rarely published directly, and even when available it's pathogen-specific (e.g. Botrytis, Penicillium) rather than commodity-specific. |

### 1. Directly checkable against literature — these are physical measurements researchers actually report, so you can look them up and compare:

- firmeza_0_default, brix_0_default, acidez_0_default — harvest-time values
- SL_ref — typical storage duration
- T_critical_high_C / T_critical_low_C — chilling injury / heat damage thresholds

For example, the search above confirms Granny Smith is commonly stored 180 days at 1°C plus a 7-day shelf life with fruit stored in a normal atmosphere at (1 ± 0.5) °C for 180 days followed by a shelf-life period of 7 days at (21 ± 1) °C — that lines up well with my SL_ref: 210 and Tref_C: 0.5. That's the kind of check you can run fruit by fruit. 

### 2. Not directly checkable — these are internal model constants, not measured quantities:

- k_firm_ref, brix_g, beta_RH, k_acidez_ref — these are rate constants specific to your kinetic model's math (first-order softening, logistic Brix rise, etc.). Papers almost never report "k" in exactly this parameterization — they report raw firmness-vs-time curves, and different labs fit different curve shapes.
- Ea_J (activation energy) — sometimes reported directly for enzymatic softening, but more often you'll only find a Q10 value in postharvest literature (how much the rate changes per 10°C). You can convert Q10 → Ea with Ea = R·ln(Q10)·T1·T2/(T2−T1), but it's an approximation, not a lookup.
- Mold parameters (mold_rate_ref, mold_sens_RH, etc.) — these are essentially never published as clean kinetic constants; postharvest pathology papers report incidence percentages under given RH/T, not rate laws like this.

## List of All Fruits and Their Parameters

### 1. Kiwi (Hayward)
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/kiwifruit)
- **Ea_J**: 40000 J/mol
- **k_firm_ref**: 0.015 1/dia
- **beta_RH**: 1.2
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/kiwifruit)
- **firmeza_min**: 2.0 N
- **firmeza_0_default**: 72.9 N - [ResearchGate](https://www.researchgate.net/publication/330048721_Non-destructive_measurement_of_fruit_firmness_to_predict_the_shelf-life_of_%27Hayward%27_kiwifruit)
- **brix_min**: 6.0
- **brix_max**: 16.5 - https://pdfs.semanticscholar.org/688c/8a091d1800d114ee66f582b7206125f9511a.pd
- **brix_g**: 0.35
- **brix_0_default**: 6.55 - https://www.sciencedirect.com/science/article/abs/pii/S0889157524006355
- **qual_firm_threshold**: 20.0 N - Tziotzios, G., Pantazi, X. E., Paraskevas, C., Tsitsopoulos, C., Valasiadis, D., Nasiopoulou, E., Michailidis, M., & Molassiotis, A. (2024). Non-Destructive Quality Estimation Using a Machine Learning-Based Spectroscopic Approach in Kiwifruits. Horticulturae, 10(3), 251. https://doi.org/10.3390/horticulturae10030251
- **qual_brix_target**: 12.5 - https://www.sciencedirect.com/science/article/abs/pii/S0925521401000977
- **acidez_0_default**: 2.0 - https://www.sciencedirect.com/science/article/abs/pii/S092552140300231X
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.2 - https://postharvest.ucdavis.edu/publication/understanding-consumer-acceptance-early-harvested-hayward-kiwifruit
- **SL_ref**: 180 dias - https://www.sciencedirect.com/science/article/abs/pii/S0925521415301642
- **T_critical_high_C**: 38.0 °C - https://www.sciencedirect.com/science/article/abs/pii/S0925521400001368
- **T_critical_low_C**: -0.01 °C - https://postharvest.ucdavis.edu/produce-facts-sheets/kiwifruit
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 92 % - https://mro.massey.ac.nz/items/e7853ff8-0c2a-4107-97e0-d9b9dc4b5eff
- **mold_rate_ref**: 0.05 1/dia
- **mold_sens_RH**: 9.0
- **mold_max_penalty**: 0.65
- **Ea_mold_J**: 43000 J/mol

### 2. Kiwi (Baby/Berry)
- **Tref_C**: 0.0 °C - Lee, U., Eo, H. J., Jung, C. R., & Kim, Y. (2025). Cold storage characteristics of hardy kiwifruit, Actinidia arguta 'Autumn Sense': comparison between two cold storage temperatures. Frontiers in plant science, 16, 1692735. https://doi.org/10.3389/fpls.2025.1692735
- **Ea_J**: 58000 J/mol
- **k_firm_ref**: 0.18 1/dia
- **beta_RH**: 2.0
- **RH_ref**: 90 % - https://www.sciencedirect.com/science/article/abs/pii/S0925521407002542
- **firmeza_min**: 1.5 N
- **firmeza_0_default**: 24.8 N - Narae Han, Hyowon Park, Chul-Woo Kim, Mun-Seop Kim & Uk Lee
(2019) Physicochemical quality of hardy kiwifruit (Actinidia arguta L. cv. Cheongsan) during
ripening is influenced by harvest maturity, Forest Science and Technology, 15:4, 187-191, DOI:
10.1080/21580103.2019.1658646
- **brix_min**: 13.0
- **brix_max**: 17.5 - Hunter, D. C., Pidakala, P. P. B., Baylis, E. M., Wohlers, M. W., Barnett, A. M., White, A., … Harker, R. (2020). Physico-chemical attributes influence consumer preferences for kiwiberries (Actinidia arguta ‘Hortgem Tahi’). New Zealand Journal of Crop and Horticultural Science, 48(3), 143–152. https://doi.org/10.1080/01140671.2020.1759111
- **brix_g**: 0.50
- **brix_0_default**: 6.5 - https://www.mdpi.com/2311-7524/11/1/105
- **qual_firm_threshold**: 5.0 N - Narae Han, Hyowon Park, Chul-Woo Kim, Mun-Seop Kim & Uk Lee
(2019) Physicochemical quality of hardy kiwifruit (Actinidia arguta L. cv. Cheongsan) during
ripening is influenced by harvest maturity, Forest Science and Technology, 15:4, 187-191, DOI:
10.1080/21580103.2019.1658646
- **qual_brix_target**: 9.40 - https://pmc.ncbi.nlm.nih.gov/articles/PMC10572923/
- **acidez_0_default**: 1.065 - Krupa, T., Tomala, K., & Zaraś-Januszkiewicz, E. (2022). Evaluation of Storage Quality of Hardy Kiwifruit (Actinidia arguta): Effect of 1-MCP and Maturity Stage. Agriculture, 12(12), 2062. https://doi.org/10.3390/agriculture12122062
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 0.77 - https://pmc.ncbi.nlm.nih.gov/articles/PMC10572923/
- **SL_ref**: 30 dias - https://www.sciencedirect.com/science/article/abs/pii/S0925521407002542
- **T_critical_high_C**: 42.0 °C - https://www.ahs.ac.cn/EN/10.16420/j.issn.0513-353x.2023-0676
- **T_critical_low_C**: -0.01 °C https://www.sciencedirect.com/science/article/abs/pii/S0304423823009640
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 % - https://apsjournals.apsnet.org/doi/10.1094/PDIS-93-11-1221A
- **mold_rate_ref**: 0.07 1/dia
- **mold_sens_RH**: 10.0
- **mold_max_penalty**: 0.75
- **Ea_mold_J**: 45000 J/mol

### 3. Kiwi Amarelo/Gold (A. chinensis)
- **Tref_C**: 1.0 °C - https://www.sciencedirect.com/science/article/abs/pii/S0925521414000866
- **Ea_J**: 42000 J/mol
- **k_firm_ref**: 0.028 1/dia
- **beta_RH**: 1.3
- **RH_ref**: 90 % - https://www.mdpi.com/2311-7524/8/2/125
- **firmeza_min**: 2.0 N
- **firmeza_0_default**: 63.8 N - https://www.sciencedirect.com/science/article/abs/pii/S0925521414000866
- **brix_min**: 8.0
- **brix_max**: 16.0 #TODO
- **brix_g**: 0.30
- **brix_0_default**: 9.5 - https://www.sciencedirect.com/science/article/abs/pii/S092552141400012X
- **qual_firm_threshold**: 10.0 N - https://www.sciencedirect.com/science/article/abs/pii/S0925521411000287
- **qual_brix_target**: 17.4 - https://patents.google.com/patent/US20100333243P1/en
- **acidez_0_default**: 1.615 - https://journals.sagepub.com/doi/10.3233/JBR-160115
- **acidez_min**: 0.4
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.1 - https://patents.google.com/patent/US20100333243P1/en
- **SL_ref**: 98 dias - https://www.sciencedirect.com/science/article/abs/pii/S0925521411002250
- **T_critical_high_C**: 25.0 °C #TODO
- **T_critical_low_C**: 0 °C - https://www.sciencedirect.com/science/article/abs/pii/S0925521414000866
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 % #TODO
- **mold_rate_ref**: 0.08 1/dia
- **mold_sens_RH**: 11.0
- **mold_max_penalty**: 0.78
- **Ea_mold_J**: 45000 J/mol

### 4. Maçã (Fuji)
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/apple-fuji)
- **Ea_J**: 47000 J/mol
- **k_firm_ref**: 0.018 1/dia
- **beta_RH**: 0.7
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/apple-fuji)
- **firmeza_min**: 15.0 N
- **firmeza_0_default**: 71 N - [Effect of methyl jasmonate treatments on the bioactive compounds and hysicochemical quality of ‘Fuji’ apple](https://www.scielo.cl/pdf/ciagr/v40n1/art18.pdf)
- **brix_min**: 13.0
- **brix_max**: 17.0 #TODO
- **brix_g**: 0.15
- **brix_0_default**: 15.0 - https://www.sciencedirect.com/science/article/abs/pii/S0925521414002956?
- **qual_firm_threshold**: 50.0 N - https://eur-lex.europa.eu/eli/C/2025/308/oj/eng
- **qual_brix_target**: 17.0 #TODO
- **acidez_0_default**: 0.405 - https://www.sciencedirect.com/science/article/abs/pii/S0925521414002956
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.5 #TODO
- **SL_ref**: 240 dias -
- **T_critical_high_C**: 45.0 °C - https://www.sciencedirect.com/science/article/pii/S0304423814004622
- **T_critical_low_C**: 1.0 °C #TODO
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 % - https://pubmed.ncbi.nlm.nih.gov/35259315/
- **mold_rate_ref**: 0.035 1/dia
- **mold_sens_RH**: 8.0
- **mold_max_penalty**: 0.55
- **Ea_mold_J**: 42000 J/mol

### 5. Maçã (Golden)
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/apple-golden-delicious)
- **Ea_J**: 44000 J/mol
- **k_firm_ref**: 0.005 1/dia
- **beta_RH**: 0.8
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/apple-golden-delicious)
- **firmeza_min**: 20.0 N
- **firmeza_0_default**: 68.13 N - Szpadzik, E., Molska-Kawulok, K., Krupa, T., & Przybyłko, S. (2024). Physico-Chemical Analysis of the Fruits and Consumer Preferences of New Apple (Malus × domestica Borkh) Hybrids Bred in Poland. Agriculture, 14(1), 1. https://doi.org/10.3390/agriculture14010001
- **brix_min**: 10.0
- **brix_max**: 17.1 - https://www.mdpi.com/2311-7524/11/3/264
- **brix_g**: 0.18
- **brix_0_default**: 13.5 - https://pmc.ncbi.nlm.nih.gov/articles/PMC8151858/
- **qual_firm_threshold**: 44.0 N - https://www.sciencedirect.com/science/article/abs/pii/S0925521402001904
- **qual_brix_target**: 12.0 - https://www.sciencedirect.com/science/article/abs/pii/S0925521402001904
- **acidez_0_default**: 0.44 - https://pmc.ncbi.nlm.nih.gov/articles/PMC8151858/
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 0.32 - https://www.sciencedirect.com/science/article/abs/pii/S0925521402001904
- **SL_ref**: 180 dias - https://postharvest.ucdavis.edu/produce-facts-sheets/apple-golden-delicious
- **T_critical_high_C**: 45.0 °C - #TODO
- **T_critical_low_C**: -1.7 °C - https://postharvest.ucdavis.edu/produce-facts-sheets/apple-golden-delicious
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 % - https://link.springer.com/article/10.1007/s11947-023-03305-9
- **mold_rate_ref**: 0.04 1/dia
- **mold_sens_RH**: 8.0
- **mold_max_penalty**: 0.60
- **Ea_mold_J**: 42000 J/mol

### 6. Maçã (Gala)
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/apple-gala)
- **Ea_J**: 24000 J/mol
- **k_firm_ref**: 0.002 1/dia
- **beta_RH**: 0.9
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/apple-golden-delicious)
- **firmeza_min**: 16.0 N
- **firmeza_0_default**: 74.5 N - Argenta, L. C., de Freitas, S. T., Mattheis, J. P., Vieira, M. J., & Ogoshi, C. (2021). Characterization and Quantification of Postharvest Losses of Apple Fruit Stored under Commercial Conditions. HortScience, 56(5), 608–616. https://doi.org/10.21273/HORTSCI15771-21
- **brix_min**: 12.0
- **brix_max**: 15.0
- **brix_g**: 0.10
- **brix_0_default**: 12.0
- **qual_firm_threshold**: 30.0 N
- **qual_brix_target**: 14.5
- **acidez_0_default**: 0.5
- **acidez_min**: 0.2
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 57 dias
- **T_critical_high_C**: 35.0 °C
- **T_critical_low_C**: -1.5 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.05 1/dia
- **mold_sens_RH**: 9.0
- **mold_max_penalty**: 0.65
- **Ea_mold_J**: 43000 J/mol

### 7. Maçã (Reineta)
- **Tref_C**: 1.5 °C - Guerra, M., Sanz, M. Á., Rodríguez-González, Á., & Casquero, P. A. (2022). Effect of Sustainable Preharvest and Postharvest Techniques on Quality and Storability of High-Acidity ‘Reinette du Canada’ Apple. Horticulturae, 8(2), 86. https://doi.org/10.3390/horticulturae8020086
- **Ea_J**: 52000 J/mol
- **k_firm_ref**: 0.035 1/dia
- **beta_RH**: 1.0
- **RH_ref**: 92 % - Guerra, M., Sanz, M. Á., Rodríguez-González, Á., & Casquero, P. A. (2022). Effect of Sustainable Preharvest and Postharvest Techniques on Quality and Storability of High-Acidity ‘Reinette du Canada’ Apple. Horticulturae, 8(2), 86. https://doi.org/10.3390/horticulturae8020086
- **firmeza_min**: 18.0 N
- **firmeza_0_default**: 92.60 N - Marcos Guerra, Miguel A Sanz, Pedro A Casquero, Influence of storage conditions on the sensory quality of a high acid apple, International Journal of Food Science and Technology, Volume 45, Issue 11, November 2010, Pages 2352–2357, https://doi.org/10.1111/j.1365-2621.2010.02410.x
- **brix_min**: 10.5
- **brix_max**: 13.5
- **brix_g**: 0.16
- **brix_0_default**: 10.5
- **qual_firm_threshold**: 35.0 N
- **qual_brix_target**: 12.5
- **acidez_0_default**: 0.8
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 90 dias
- **T_critical_high_C**: 35.0 °C
- **T_critical_low_C**: -1.5 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.05 1/dia
- **mold_sens_RH**: 9.0
- **mold_max_penalty**: 0.65
- **Ea_mold_J**: 43000 J/mol

### 8. Maçã (Granny Smith)
- **Tref_C**: 0.5 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/apple-granny-smith)
- **Ea_J**: 40000 J/mol
- **k_firm_ref**: 0.006 1/dia
- **beta_RH**: 0.6
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/apple-granny-smith)
- **firmeza_min**: 25.0 N
- **firmeza_0_default**: 71.3 N - [ResearchGate](https://www.researchgate.net/publication/257355990_Utilizing_the_IAD_index_to_determine_internal_quality_attributes_of_apples_at_harvest_and_after_storage)
- **brix_min**: 10.0
- **brix_max**: 13.0
- **brix_g**: 0.10
- **brix_0_default**: 11.5
- **qual_firm_threshold**: 55.0 N
- **qual_brix_target**: 12.5
- **acidez_0_default**: 0.75
- **acidez_min**: 0.6
- **k_acidez_ref**: 0.015 1/dia
- **Ea_acidez_J**: 50000 J/mol
- **qual_acidez_target**: 1.8
- **SL_ref**: 210 dias
- **T_critical_high_C**: 30.0 °C
- **T_critical_low_C**: -1.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.03 1/dia
- **mold_sens_RH**: 7.5
- **mold_max_penalty**: 0.50
- **Ea_mold_J**: 41000 J/mol

### 9. Maçã (Red Delicious)
- **Tref_C**: 0.5 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/apple-red-delicious)
- **Ea_J**: 44000 J/mol
- **k_firm_ref**: 0.014 1/dia
- **beta_RH**: 0.8
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/apple-red-delicious)
- **firmeza_min**: 12.0 N
- **firmeza_0_default**: 73 N - [ResearchGate](https://www.researchgate.net/publication/277995465_Harvest_Maturity_Storage_Temperature_and_1-MCP_Application_Frequency_Alter_Firmness_Retention_and_Chlorophyll_Fluorescence_of_Redchief_Delicious%27_Apples)
- **brix_min**: 11.0
- **brix_max**: 14.0
- **brix_g**: 0.14
- **brix_0_default**: 12.0
- **qual_firm_threshold**: 40.0 N
- **qual_brix_target**: 13.0
- **acidez_0_default**: 0.3
- **acidez_min**: 0.15
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 0.35
- **SL_ref**: 150 dias
- **T_critical_high_C**: 30.0 °C
- **T_critical_low_C**: 0.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.05 1/dia
- **mold_sens_RH**: 9.0
- **mold_max_penalty**: 0.65
- **Ea_mold_J**: 43000 J/mol

### 10. Maçã (Bravo de Esmolfe)
- **Tref_C**: 2.0 °C - [ResearchGate](https://www.researchgate.net/publication/222431759_Modified_atmosphere_package_for_apple_'Bravo_de_Esmolfe')
- **Ea_J**: 50000 J/mol
- **k_firm_ref**: 0.030 1/dia
- **beta_RH**: 1.1
- **RH_ref**: 85 % - [ResearchGate](https://www.researchgate.net/publication/222431759_Modified_atmosphere_package_for_apple_'Bravo_de_Esmolfe')
- **firmeza_min**: 12.0 N
- **firmeza_0_default**: 74.6 N - https://comum.rcaap.pt/server/api/core/bitstreams/47f2f262-7ab3-4129-b168-46d779c98e8e/content?
- **brix_min**: 12.0
- **brix_max**: 15.0
- **brix_g**: 0.15
- **brix_0_default**: 12.5
- **qual_firm_threshold**: 25.0 N
- **qual_brix_target**: 14.0
- **acidez_0_default**: 0.6
- **acidez_min**: 0.4
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 52000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 75 dias
- **T_critical_high_C**: 28.0 °C
- **T_critical_low_C**: -1.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 94.0 %
- **mold_rate_ref**: 0.09 1/dia
- **mold_sens_RH**: 12.0
- **mold_max_penalty**: 0.78
- **Ea_mold_J**: 46000 J/mol

### 11. Maçã (Royal Gold) - No information
- **Tref_C**: 1.5 °C - 
- **Ea_J**: 45000 J/mol
- **k_firm_ref**: 0.006 1/dia
- **beta_RH**: 0.75
- **RH_ref**: 95 %
- **firmeza_min**: 20.0 N
- **firmeza_0_default**: 72 N
- **brix_min**: 11.0
- **brix_max**: 15.0
- **brix_g**: 0.17
- **brix_0_default**: 11.5
- **qual_firm_threshold**: 48.0 N
- **qual_brix_target**: 14.0
- **acidez_0_default**: 0.45
- **acidez_min**: 0.3
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 0.9
- **SL_ref**: 150 dias
- **T_critical_high_C**: 35.0 °C
- **T_critical_low_C**: 0.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.04 1/dia
- **mold_sens_RH**: 8.0
- **mold_max_penalty**: 0.60
- **Ea_mold_J**: 42000 J/mol

### 12. Maçã (Pink Lady)
- **Tref_C**: 0 °C - Muhammad Shafiq, Zora Singh, Ahmad S Khan, Delayed harvest and cold storage period influence ethylene production, fruit firmness and quality of ‘Cripps Pink’ apple, International Journal of Food Science and Technology, Volume 46, Issue 12, December 2011, Pages 2520–2529, https://doi.org/10.1111/j.1365-2621.2011.02776.x
- **Ea_J**: 38000 J/mol
- **k_firm_ref**: 0.005 1/dia
- **beta_RH**: 0.65
- **RH_ref**: 92 % - Muhammad Shafiq, Zora Singh, Ahmad S Khan, Delayed harvest and cold storage period influence ethylene production, fruit firmness and quality of ‘Cripps Pink’ apple, International Journal of Food Science and Technology, Volume 46, Issue 12, December 2011, Pages 2520–2529, https://doi.org/10.1111/j.1365-2621.2011.02776.x
- **firmeza_min**: 22.0 N
- **firmeza_0_default**: 72.2 N - [ResearchGate](https://www.researchgate.net/publication/257355990_Utilizing_the_IAD_index_to_determine_internal_quality_attributes_of_apples_at_harvest_and_after_storage)
- **brix_min**: 13.0
- **brix_max**: 16.0
- **brix_g**: 0.12
- **brix_0_default**: 13.5
- **qual_firm_threshold**: 55.0 N
- **qual_brix_target**: 15.0
- **acidez_0_default**: 0.55
- **acidez_min**: 0.4
- **k_acidez_ref**: 0.015 1/dia
- **Ea_acidez_J**: 50000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 240 dias
- **T_critical_high_C**: 30.0 °C
- **T_critical_low_C**: -1.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.03 1/dia
- **mold_sens_RH**: 7.5
- **mold_max_penalty**: 0.50
- **Ea_mold_J**: 41000 J/mol

### 13. Maçã (Jonagold)
- **Tref_C**: 0.5 °C - Prange, R. K., & Wright, A. H. (2023). A Review of Storage Temperature Recommendations for Apples and Pears. Foods, 12(3), 466. https://doi.org/10.3390/foods12030466
- **Ea_J**: 46000 J/mol
- **k_firm_ref**: 0.016 1/dia
- **beta_RH**: 0.85
- **RH_ref**: 95 % - https://pmc.ncbi.nlm.nih.gov/articles/PMC8882757/
- **firmeza_min**: 14.0 N
- **firmeza_0_default**: 69.3 N - https://edepot.wur.nl/476160
- **brix_min**: 12.0
- **brix_max**: 15.5
- **brix_g**: 0.16
- **brix_0_default**: 12.5
- **qual_firm_threshold**: 38.0 N
- **qual_brix_target**: 14.5
- **acidez_0_default**: 0.5
- **acidez_min**: 0.35
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 0.9
- **SL_ref**: 130 dias
- **T_critical_high_C**: 30.0 °C
- **T_critical_low_C**: 0.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.05 1/dia
- **mold_sens_RH**: 9.0
- **mold_max_penalty**: 0.65
- **Ea_mold_J**: 43000 J/mol

### 14. Maçã (Alcobaça) - Diversas Espécies
- **Tref_C**: 2.0 °C
- **Ea_J**: 48000 J/mol
- **k_firm_ref**: 0.020 1/dia
- **beta_RH**: 0.9
- **RH_ref**: 92 %
- **firmeza_min**: 18.0 N
- **firmeza_0_default**: 68 N
- **brix_min**: 11.0
- **brix_max**: 14.0
- **brix_g**: 0.15
- **brix_0_default**: 11.5
- **qual_firm_threshold**: 38.0 N
- **qual_brix_target**: 13.0
- **acidez_0_default**: 0.55
- **acidez_min**: 0.4
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 53000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 120 dias
- **T_critical_high_C**: 32.0 °C
- **T_critical_low_C**: -1.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.05 1/dia
- **mold_sens_RH**: 9.0
- **mold_max_penalty**: 0.65
- **Ea_mold_J**: 43000 J/mol

### 15. Morango
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/strawberry)
- **Ea_J**: 52000 J/mol
- **k_firm_ref**: 0.0012 1/dia
- **beta_RH**: 2.4
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/strawberry)
- **firmeza_min**: 1.0 N
- **firmeza_0_default**: 3.87 N - Błaszczyk, J., Bieniasz, M., Nawrocki, J., Kopeć, M., Mierzwa-Hersztek, M., Gondek, K., Zaleski, T., Knaga, J., & Bogdał, S. (2022). The Effect of Harvest Date and Storage Conditions on the Quality of Remontant Strawberry Cultivars Grown in a Gutter System under Covers. Agriculture, 12(8), 1193. https://doi.org/10.3390/agriculture12081193
- **brix_min**: 5.0
- **brix_max**: 9.0
- **brix_g**: 0.3
- **brix_0_default**: 7.5
- **qual_firm_threshold**: 2.0 N
- **qual_brix_target**: 9.0
- **acidez_0_default**: 0.8
- **acidez_min**: 0.2
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 7 dias
- **T_critical_high_C**: 10.0 °C
- **T_critical_low_C**: -1.1 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 93.0 %
- **mold_rate_ref**: 0.22 1/dia
- **mold_sens_RH**: 16.0
- **mold_max_penalty**: 0.95
- **Ea_mold_J**: 52000 J/mol

### 16. Framboesa
- **Tref_C**: 0.0 °C - Chien Y Wang, Maintaining postharvest quality of raspberries with natural volatile compounds, International Journal of Food Science and Technology, Volume 38, Issue 8, December 2003, Pages 869–875, https://doi.org/10.1046/j.0950-5423.2003.00758.x
- **Ea_J**: 56000 J/mol
- **k_firm_ref**: 0.060 1/dia
- **beta_RH**: 2.2
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/ar/produce-facts-sheets/bushberry)
- **firmeza_min**: 1.5 N
- **firmeza_0_default**: 2.51 N - https://www.ars.usda.gov/ARSUserFiles/1718/PDF/2001/Lewismanuscript.pdf
- **brix_min**: 9.5
- **brix_max**: 10.0
- **brix_g**: 0.01
- **brix_0_default**: 9.5
- **qual_firm_threshold**: 2.5 N
- **qual_brix_target**: 9.5
- **acidez_0_default**: 1.2
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 7 dias
- **T_critical_high_C**: 10.0 °C
- **T_critical_low_C**: -1.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 93.0 %
- **mold_rate_ref**: 0.20 1/dia
- **mold_sens_RH**: 16.0
- **mold_max_penalty**: 0.95
- **Ea_mold_J**: 52000 J/mol

### 17. Mirtilo
- **Tref_C**: 0.0 °C - Nunes, M. C. N., Emond, J. P., & Brecht, J. K. (2004). Quality Curves for Highbush Blueberries as a Function of the Storage Temperature. Small Fruits Review, 3(3–4), 423–440. https://doi.org/10.1300/J301v03n03_18
- **Ea_J**: 42000 J/mol
- **k_firm_ref**: 0.030 1/dia
- **beta_RH**: 1.6
- **RH_ref**: 90 % - A.C. Paniagua, A.R. East, J.A. Heyes, Interaction of temperature control deficiencies and atmosphere conditions during blueberry storage on quality outcomes, Postharvest Biology and Technology, Volume 95, 2014, Pages 50-59, ISSN 0925-5214, https://doi.org/10.1016/j.postharvbio.2014.04.006.
- **firmeza_min**: 3.0 N
- **firmeza_0_default**: 6.49 N - Kim, J. G., Kim, H. L., Kim, S. J., & Park, K. S. (2013). Fruit quality, anthocyanin and total phenolic contents, and antioxidant activities of 45 blueberry cultivars grown in Suwon, Korea. Journal of Zhejiang University. Science. B, 14(9), 793–799. https://doi.org/10.1631/jzus.B1300012
- **brix_min**: 11.5
- **brix_max**: 14.0
- **brix_g**: 0.02
- **brix_0_default**: 11.5
- **qual_firm_threshold**: 4.0 N
- **qual_brix_target**: 11.5
- **acidez_0_default**: 0.6
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.009 1/dia
- **Ea_acidez_J**: 30000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 21 dias
- **T_critical_high_C**: 8.0 °C
- **T_critical_low_C**: -1.5 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 94.0 %
- **mold_rate_ref**: 0.12 1/dia
- **mold_sens_RH**: 14.0
- **mold_max_penalty**: 0.90
- **Ea_mold_J**: 48000 J/mol

### 18. Cereja
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/cherry)
- **Ea_J**: 48000 J/mol
- **k_firm_ref**: 0.045 1/dia
- **beta_RH**: 1.6
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/cherry)
- **firmeza_min**: 8.0 N
- **firmeza_0_default**: 16.5 N - Dziedzic, E., Błaszczyk, J. Evaluation of sweet cherry fruit quality after short-term storage in relation to the rootstock. Hortic. Environ. Biotechnol. 60, 925–934 (2019). https://doi.org/10.1007/s13580-019-00184-y
- **brix_min**: 16.0
- **brix_max**: 16.5
- **brix_g**: 0.01
- **brix_0_default**: 16.0
- **qual_firm_threshold**: 10.0 N
- **qual_brix_target**: 16.0
- **acidez_0_default**: 0.5
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 21 dias
- **T_critical_high_C**: 35.0 °C
- **T_critical_low_C**: -1.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 94.0 %
- **mold_rate_ref**: 0.10 1/dia
- **mold_sens_RH**: 13.0
- **mold_max_penalty**: 0.85
- **Ea_mold_J**: 47000 J/mol

### 19. Pêssego
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/peach)
- **Ea_J**: 56000 J/mol
- **k_firm_ref**: 0.080 1/dia
- **beta_RH**: 1.1
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/peach)
- **firmeza_min**: 4.0 N
- **firmeza_0_default**: 47.5 N - Rita G. Gonçalves, João Couto, Domingos P.F. Almeida, On-tree maturity control of peach cultivars: Comparison between destructive and nondestructive harvest indices, Scientia Horticulturae, Volume 209, 2016, Pages 293-299, ISSN 0304-4238, https://doi.org/10.1016/j.scienta.2016.06.040
- **brix_min**: 10.0
- **brix_max**: 14.0
- **brix_g**: 0.20
- **brix_0_default**: 10.0
- **qual_firm_threshold**: 8.0 N
- **qual_brix_target**: 13.0
- **acidez_0_default**: 0.6
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 14 dias
- **T_critical_high_C**: 30.0 °C
- **T_critical_low_C**: -2.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 94.0 %
- **mold_rate_ref**: 0.10 1/dia
- **mold_sens_RH**: 12.0
- **mold_max_penalty**: 0.85
- **Ea_mold_J**: 48000 J/mol

### 20. Ameixa
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/plum)
- **Ea_J**: 52000 J/mol
- **k_firm_ref**: 0.1 1/dia
- **beta_RH**: 1.0
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/plum)
- **firmeza_min**: 0.0 N
- **firmeza_0_default**: 31 N - Minas IS, Font i Forcada C, Dangl GS, Gradziel TM, Dandekar AM and Crisosto CH (2015) Discovery of non-climacteric and suppressed climacteric bud sport mutations originating from a climacteric Japanese plum cultivar (Prunus salicina Lindl.). Front. Plant Sci. 6:316. doi: 10.3389/fpls.2015.00316
- **brix_min**: 10.0
- **brix_max**: 16.0
- **brix_g**: 0.25
- **brix_0_default**: 10.0
- **qual_firm_threshold**: 10.0 N
- **qual_brix_target**: 15.0
- **acidez_0_default**: 0.8
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.175
- **SL_ref**: 21 dias
- **T_critical_high_C**: 30.0 °C
- **T_critical_low_C**: 8.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 94.0 %
- **mold_rate_ref**: 0.09 1/dia
- **mold_sens_RH**: 12.0
- **mold_max_penalty**: 0.82
- **Ea_mold_J**: 47000 J/mol

### 21. Laranja
- **Tref_C**: 5.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/orange)
- **Ea_J**: 42000 J/mol
- **k_firm_ref**: 0.010 1/dia
- **beta_RH**: 0.35
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/orange)
- **firmeza_min**: 20.0 N
- **firmeza_0_default**: 24.16 N -  Virkar A.M., Garande V.K. (2023). Effect of Different Post-harvest Treatments on Shelf Life and Quality of Sweet Orange (Citrus sinensis Osbeck.) Fruit#. Asian Journal of Dairy and Food Research.. doi: 10.18805/ajdfr.DR-2118.
- **brix_min**: 11.0
- **brix_max**: 14.0
- **brix_g**: 0.01
- **brix_0_default**: 11.0
- **qual_firm_threshold**: 35.0 N
- **qual_brix_target**: 13.0
- **acidez_0_default**: 1.0
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.005 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 60 dias
- **T_critical_high_C**: 35.0 °C
- **T_critical_low_C**: 3.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 96.0 %
- **mold_rate_ref**: 0.03 1/dia
- **mold_sens_RH**: 8.0
- **mold_max_penalty**: 0.50
- **Ea_mold_J**: 42000 J/mol

### 22. Banana
- **Tref_C**: 13.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/banana)
- **Ea_J**: 42000 J/mol
- **k_firm_ref**: 0.010 1/dia
- **beta_RH**: 0.35
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/orange)
- **firmeza_min**: 20.0 N
- **firmeza_0_default**: 79.1 N - https://pmc.ncbi.nlm.nih.gov/articles/PMC3551045
- **brix_min**: 11.0
- **brix_max**: 14.0
- **brix_g**: 0.01
- **brix_0_default**: 11.0
- **qual_firm_threshold**: 35.0 N
- **qual_brix_target**: 12.0
- **acidez_0_default**: 1.0
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 90 dias
- **T_critical_high_C**: 35.0 °C
- **T_critical_low_C**: 13.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.06 1/dia
- **mold_sens_RH**: 10.0
- **mold_max_penalty**: 0.80
- **Ea_mold_J**: 45000 J/mol

### 23. Pera
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/pear-bartlett)
- **Ea_J**: 54000 J/mol
- **k_firm_ref**: 0.050 1/dia
- **beta_RH**: 1.2
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/pear-bartlett)
- **firmeza_min**: 6.0 N
- **firmeza_0_default**: 55 N - https://www.sciencedirect.com/science/article/abs/pii/S0925521408002433
- **brix_min**: 11.0
- **brix_max**: 15.0
- **brix_g**: 0.25
- **brix_0_default**: 11.0
- **qual_firm_threshold**: 12.0 N
- **qual_brix_target**: 14.0
- **acidez_0_default**: 0.3
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 90 dias
- **T_critical_high_C**: 35.0 °C
- **T_critical_low_C**: -2.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.07 1/dia
- **mold_sens_RH**: 10.0
- **mold_max_penalty**: 0.75
- **Ea_mold_J**: 45000 J/mol

### 24. Uva
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/grape)
- **Ea_J**: 45000 J/mol
- **k_firm_ref**: 0.020 1/dia
- **beta_RH**: 1.8
- **RH_ref**: 90.0 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/grape)
- **firmeza_min**: 5.0 N
- **firmeza_0_default**: 3.55 N - https://reference-global.com/article/10.2478/johr-2020-0005
- **brix_min**: 16.0
- **brix_max**: 16.5
- **brix_g**: 0.01
- **brix_0_default**: 16.0
- **qual_firm_threshold**: 8.0 N
- **qual_brix_target**: 16.0
- **acidez_0_default**: 0.6
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 25 dias
- **T_critical_high_C**: 35.0 °C
- **T_critical_low_C**: -2.7 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.10 1/dia
- **mold_sens_RH**: 14.0
- **mold_max_penalty**: 0.90
- **Ea_mold_J**: 46000 J/mol

### 25. Figo
- **Tref_C**: 0.0 °C - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/fig)
- **Ea_J**: 52000 J/mol
- **k_firm_ref**: 0.110 1/dia
- **beta_RH**: 1.8
- **RH_ref**: 90 % - [postharvest.ucdavis.edu](https://postharvest.ucdavis.edu/produce-facts-sheets/fig)
- **firmeza_min**: 1.0 N
- **firmeza_0_default**: 3.46 N - Waghmare, R. B., & Annapure, U. S. (2018). Integrated effect of radiation processing and modified atmosphere packaging (MAP) on shelf life of fresh fig. Journal of food science and technology, 55(6), 1993–2002. https://doi.org/10.1007/s13197-018-3113-2
- **brix_min**: 16.0
- **brix_max**: 20.0
- **brix_g**: 0.15
- **brix_0_default**: 16.0
- **qual_firm_threshold**: 2.0 N
- **qual_brix_target**: 19.0
- **acidez_0_default**: 0.3
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 7 dias
- **T_critical_high_C**: 35.0 °C
- **T_critical_low_C**: -2.0 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 93.0 %
- **mold_rate_ref**: 0.18 1/dia
- **mold_sens_RH**: 14.0
- **mold_max_penalty**: 0.92
- **Ea_mold_J**: 50000 J/mol

### 26. Melão (Piel de Sapo)
- **Tref_C**: 8.0 °C - Fernández-Trujillo, J. P., Obando, J., Martínez, J. A., Alarcón, A. L., Eduardo, I., Arús, P., & Monforte, A. J. (2007). Mapping Fruit Susceptibility to Postharvest Physiological Disorders and Decay Using a Collection of Near-isogenic Lines of Melon. Journal of the American Society for Horticultural Science, 132(5), 739–748. https://doi.org/10.21273/JASHS.132.5.739
- **Ea_J**: 52000 J/mol
- **k_firm_ref**: 0.060 1/dia
- **beta_RH**: 0.9
- **RH_ref**: 85 % - Correa, E. C., Castillejo, N., Barreiro, P., Diezma, B., Garrido-Izard, M., Barbosa Menezes, J., & Aguayo, E. (2023). Environmental and Qualitative Monitoring of a Transoceanic Intermodal Transport of Melons. Agronomy, 13(1), 33. https://doi.org/10.3390/agronomy13010033
- **firmeza_min**: 5.0 N
- **firmeza_0_default**: 27 N - Nunes, G. H. de S., Pereira, E. W., Sales Júnior, R., Bezerra Neto, F., Oliveira, K. C. de ., & Mesquita, L. X.. (2008). Produtividade e qualidade de frutos de melão pele-de-sapo em duas densidades de plantio. Horticultura Brasileira, 26(2), 236–239. https://doi.org/10.1590/S0102-05362008000200021
- **brix_min**: 10.0
- **brix_max**: 14.0
- **brix_g**: 0.22
- **brix_0_default**: 10.0
- **qual_firm_threshold**: 8.0 N
- **qual_brix_target**: 13.5
- **acidez_0_default**: 0.2
- **acidez_min**: 0.5
- **k_acidez_ref**: 0.02 1/dia
- **Ea_acidez_J**: 55000 J/mol
- **qual_acidez_target**: 1.0
- **SL_ref**: 21 dias
- **T_critical_high_C**: 35.0 °C
- **T_critical_low_C**: 2.2 °C
- **T_critical_high_rate**: 0
- **T_critical_low_rate**: 0
- **RH_mold_thr**: 95.0 %
- **mold_rate_ref**: 0.08 1/dia
- **mold_sens_RH**: 10.0
- **mold_max_penalty**: 0.78
- **Ea_mold_J**: 45000 J/mol
