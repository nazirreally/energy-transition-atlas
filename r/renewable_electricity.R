# Observed electricity generation share trends from OWID; no simulated records.
# Run: Rscript r/renewable_electricity.R
suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
  library(ggplot2)
})
url <- 'https://ourworldindata.org/grapher/electricity-mix.csv?v=1&csvType=full&useColumnShortNames=false&frequency=annual&metric=share_of_generation&source=renewables'
raw <- read.csv(url, check.names=FALSE)
required <- c('Entity','Code','Year')
if (!all(required %in% names(raw))) stop('OWID CSV schema changed')
value_cols <- setdiff(names(raw),required)
if (length(value_cols)!=1) stop('Ambiguous OWID metric column')
names(raw)[names(raw)==value_cols] <- 'renewable_share'
observed <- raw |>
  transmute(country=Entity,iso3=Code,year=as.integer(Year),
            renewable_share=as.numeric(renewable_share)) |>
  filter(!is.na(renewable_share),nchar(iso3)==3) |>
  arrange(country,year) |>
  group_by(country) |>
  mutate(previous_year=lag(year),
         change_pp=if_else(year-previous_year==1,
                           renewable_share-lag(renewable_share),NA_real_)) |>
  ungroup()
if (nrow(observed)==0) stop('No published observations available')
dir.create('outputs',showWarnings=FALSE)
write.csv(observed,'outputs/renewables_observed.csv',row.names=FALSE)
selected <- observed |>
  filter(country %in% c('Pakistan','India','Germany','Brazil','United States'))
if (nrow(selected)>0) {
  chart <- ggplot(selected,aes(year,renewable_share,color=country)) +
    geom_line(linewidth=0.9,na.rm=TRUE) +
    labs(title='Observed renewable share of electricity',
         x='Year',y='Share (%)',color='Country',
         caption='Our World in Data electricity-mix Grapher; no interpolation') +
    theme_minimal(base_size=13)
  ggsave('outputs/renewables_observed.png',chart,width=11,height=6,dpi=160)
}
cat(sprintf('Observed rows: %d; countries: %d; years: %d-%d\n',
            nrow(observed),n_distinct(observed$iso3),
            min(observed$year),max(observed$year)))
