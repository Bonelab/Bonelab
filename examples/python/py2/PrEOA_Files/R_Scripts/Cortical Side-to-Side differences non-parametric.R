
# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Stats/Full_ROI_Participant_Characteristics/Data_Final_June_2017")
library(data.table)
library(etable)
library(xtable)

# read in csv
Control <- read.csv("Control_differences.csv",stringsAsFactor=F)
Injured <- read.csv("Injured_differences.csv",stringsAsFactor=F)

pairedtest <-list()
vari1 <- list()
median_GI <- list()
median_GC <- list()
IQRI <- list()
IQRC <- list()
Group_comparison <- list()

vari1 <- c("Ct.vBMD1_LF",	"Ct.Po1_LF",	"Ct.Th1_LF",	"Ct.vBMD1_FM",	"Ct.Po1_FM",	"Ct.Th1_FM",	"Ct.vBMD1_LT",	"Ct.Po1_LT",	"Ct.Th1_LT",	"Ct.vBMD1_MT",	"Ct.Po1_MT",	"Ct.Th1_MT")

for(i in 1:12)
{
  Group_comparison[[i]] <- wilcox.test(Control[[vari1[i]]],Injured[[vari1[i]]], na.rm = TRUE, paired =FALSE)
  IQRI[[i]] <- quantile(Injured[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  IQRC[[i]] <- quantile(Control[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
}

Group_comp <- sapply(Group_comparison, function(x) {
  c(name = x$data.name,
    p.value = x$p.value)
})



table2 <- list()
table2[["ID"]] <- vari1  
table2[["IQR I"]] <- IQRI
table2[["IQR C"]] <- IQRC
table2[["GroupH P Values"]] <- Group_comp["p.value",]
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "temp.csv")