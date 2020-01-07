# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Stats/Full_ROI")
library(data.table)
library(etable)
library(xtable)

# read in csv
# read in csv
Left <- read.csv("Measurements_Left_Control.csv",stringsAsFactor=F)
Right <- read.csv("Measurements_Right_Control.csv",stringsAsFactor=F)
Injured <- read.csv("Measurements_Injured.csv",stringsAsFactor=F)
Contralateral <- read.csv("Measurements_Contralateral.csv",stringsAsFactor=F)
Control <- read.csv("Measurements_All_Control.csv",stringsAsFactor=F)

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

vari1 <- c("moaks_i_bml",	"moaks_i_cartilage",	"moaks_i_synovitis",	"moaks_i_meniscal",	"moaks_i_score",	"moaks_i_lig",	"moaks_i_rating")

for(i in 1:7)
{
  IQRI[[i]] <- quantile(Injured[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  IQRC[[i]] <- quantile(Contralateral[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  IQRL[[i]] <- quantile(Left[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  IQRR[[i]] <- quantile(Right[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
}

table2 <- list()
table2[["ID"]] <- vari1  
table2[["IQR I"]] <- IQRI
table2[["IQR C"]] <- IQRC
table2[["IQR L"]] <- IQRL
table2[["IQR R"]] <- IQRR
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "MOAKS_data.csv")