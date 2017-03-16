#!/usr/bin/env Rscript

intrust = '"tract","FAmean_mean","FAmean_sd","num_mean","num_sd","count"
"af.left",714.182544932399,30.4676278440711,433.140625,257.950520516233,384
"af.right",696.470852774055,34.8401036745462,441.361038961039,290.948014111773,385
"ioff.left",714.685249908589,30.4187930443161,131.124675324675,105.584410539235,385
"ioff.right",707.633674637833,30.0749770765204,201.296875,135.805998900886,384
"slf_iii.left",666.308324741928,29.5571559220112,656.311688311688,344.504930863216,385
"slf_iii.right",660.472731188003,30.0607433890063,856.412987012987,439.223181852611,385
"slf_ii.left",659.341421059491,32.6647141147986,339.862337662338,257.711077039572,385
"slf_ii.right",660.085906472326,30.9626825136909,356.722077922078,271.30096133385,385
"slf_i.left",591.851359327127,40.0703509639063,452.316883116883,264.787696699815,385
"slf_i.right",580.02563236122,39.589693983944,278.345454545455,200.974326294543,385
"uf.left",589.85265447185,42.8613369562814,195.744125326371,174.371158305798,383
"uf.right",565.9559476129,43.1105907847185,142.316883116883,126.637537840325,385
'
con <- textConnection(intrust)
csv.intrust <- read.csv(con)
close(con)

require(data.table)
args = commandArgs(trailingOnly=TRUE)
d <- fread(args[1])
ds <- d[grep("af|uf|slf|ioff",d$tract),.(FAmean_mean=mean(FA_mean),FAmean_sd=sd(FA_mean),num_mean=mean(num),num_sd=sd(num),count=length(caseid)),by=tract]
setorder(ds, tract)
if (length(args) > 1) {
    cat(paste0("Make ", args[2]), "\n")
    write.csv(ds,args[2],row.names=F)
    cat("Done.\n")
} else {
    ds
}

if (length(args) > 2) {
    cat(paste0("Make ", args[3]), "\n")
    write.csv(csv.intrust,args[3],row.names=F)
    cat("Done.\n")
} else {
  cat("Compare to Intrust:\n")
  csv.intrust
}
