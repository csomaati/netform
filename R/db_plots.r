library(RMySQL)
args = commandArgs(trailingOnly=TRUE)
if (length(args)==0) {
  stop("At least one argument must be supplied (input file).n", call.=FALSE)
}
measurement.id <- args[1]
m <- dbDriver("MySQL")
conn <- dbConnect(m, group = "logging-db", default.file='/mnt/ADAT/netform/valley_free/scripts/R/my.cnf')

vf.histogram.perend.query <- paste("
SELECT CONCAT(s, '-', t) as st, sum(v4) as isvf, count(v4) - sum(v4) as nonvf
FROM results
WHERE result_type = 'PERPATHREAL'
  AND measurement_id = '", measurement.id, "'
GROUP BY st
ORDER BY isvf DESC
", sep="")

vf.histogram.perend.values <- dbGetQuery(conn, vf.histogram.perend.query)
file.remove('vfperend.jpg')
jpeg('vfperend.jpg')
barplot(vf.histogram.perend.values$isvf, main='VF route count/endponints',
        xlab='endpoints', ylab='count')
dev.off()

file.remove('nonvfperend.jpg')
jpeg('nonvfperend.jpg')
barplot(vf.histogram.perend.values$nonvf,
        main='NONVF route count/endponints',
        xlab='endpoints', ylab='count')
dev.off()
