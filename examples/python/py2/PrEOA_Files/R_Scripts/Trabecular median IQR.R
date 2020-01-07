# Read in data

# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Stats/Trabecular/Bottom_Layer")
library(data.table)
library(etable)
library(xtable)

# read in csv
Left <- read.csv("Left.csv",stringsAsFactor=F)
Right <- read.csv("Right.csv",stringsAsFactor=F)
Injured <- read.csv("Injured.csv",stringsAsFactor=F)
Contralateral <- read.csv("Contralateral.csv",stringsAsFactor=F)

pairedtest <-list()
vari1 <- list()
median_GI <- list()
median_GC <- list()
IQRI <- list()
IQRC <- list()
median_GL <- list()
median_GR <- list()
IQRL <- list()
IQRR <- list()
GroupI_comparison <- list()
GroupC_comparison <- list()

vari1 <- c("Tot.vBMD1_LF",	"Tb.Ar1_LF",	"Tb.vBMD1_LF",	"Tb.BV.TV1_LF",	"Tb.N1_LF",	"Tb.Th1_LF",	"Tb.Sp1_LF",	"Tot.vBMD1_LT",	"Tb.Ar1_LT",	"Tb.vBMD1_LT",	"Tb.BV.TV1_LT",	"Tb.N1_LT",	"Tb.Th1_LT",	"Tb.Sp1_LT",	"Tot.vBMD1_FM",	"Tb.Ar1_FM",	"Tb.vBMD1_FM",	"Tb.BV.TV1_FM",	"Tb.N1_FM",	"Tb.Th1_FM",	"Tb.Sp1_FM",	"Tot.vBMD1_TM",	"Tb.Ar1_TM",	"Tb.vBMD1_TM",	"Tb.BV.TV1_TM",	"Tb.N1_TM",	"Tb.Th1_TM",	"Tb.Sp1_TM")

for(i in 1:28)
{
  GroupC_comparison[[i]] <- wilcox.test(Left[[vari1[i]]],Right[[vari1[i]]], na.rm = TRUE, paired =TRUE)
  GroupI_comparison[[i]] <- wilcox.test(Injured[[vari1[i]]],Contralateral[[vari1[i]]], na.rm = TRUE, paired =TRUE)
  IQRI[[i]] <- quantile(Injured[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  IQRC[[i]] <- quantile(Contralateral[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  IQRL[[i]] <- quantile(Left[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  IQRR[[i]] <- quantile(Right[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
}

GroupC_comp <- sapply(GroupC_comparison, function(x) {
  c(name = x$data.name,
    p.value = x$p.value)
})

GroupI_comp <- sapply(GroupI_comparison, function(x) {
  c(name = x$data.name,
    p.value = x$p.value)
})

table2 <- list()
table2[["ID"]] <- vari1  
table2[["IQR I"]] <- IQRI
table2[["IQR C"]] <- IQRC
table2[["IQR L"]] <- IQRL
table2[["IQR R"]] <- IQRR
table2[["GroupI P Values"]] <- GroupI_comp["p.value",]
table2[["GroupH P Values"]] <- GroupC_comp["p.value",]
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "median_iqr_trabecular.csv")
