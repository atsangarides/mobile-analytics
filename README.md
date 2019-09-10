# mobile-analytics
A compilation of modules for calculating key app usage metrics using nothing but python.
 
## stats
Module containing all the functions needed to calculate the different metrics.
* acquisition: calculation of new/active/returning users and growth stats per period
* retention: retention of users per period per cohort
* funnel: funnel analysis for a list of events

## visualisations
Module containing all the plotting functions. These make use of the functions included in the `stats` module.
* growth: visualisation of growth stats <img src="/static/growth.png" alt="" height="400" width="400">
* retention_plots: retention plot <img src="/static/retention.png" alt="">
* funnel-plots: single/stacked funnel plot <img src="/static/funnel.png" alt="">

