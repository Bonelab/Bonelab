# Read in data

# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Stats/Full_ROI")
library(data.table)
library(etable)
library(xtable)

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
median_GControl <- list()
IQRControl <- list()

vari1 <- c("Th_LC_F",	"SD_LC_F",	"Max_LC_F",	"Th_MC_F",	"SD_MC_F",	"Max_MC_F",	"Th_LC_T",	"SD_LC_T",	"Max_LC_T",	"Th_MC_T",	"SD_MC_T",	"Max_MC_T",	"Age1",	"Ct.vBMD1_LF",	"Ct.Po1_LF",	"Ct.Th1_LF",	"Ct.vBMD1_FM",	"Ct.Po1_FM",	"Ct.Th1_FM",	"Ct.vBMD1_LT",	"Ct.Po1_LT",	"Ct.Th1_LT",	"Ct.vBMD1_MT",	"Ct.Po1_MT",	"Ct.Th1_MT")

for(i in 1:24)
{
  median_GI[[i]] <- median(Injured[[vari1[i]]], na.rm = TRUE)
  IQRI[[i]] <- quantile(Injured[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  median_GC[[i]] <- median(Contralateral[[vari1[i]]], na.rm = TRUE)
  IQRC[[i]] <- quantile(Contralateral[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  median_GL[[i]] <- median(Left[[vari1[i]]], na.rm = TRUE)
  IQRL[[i]] <- quantile(Left[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  median_GR[[i]] <- median(Right[[vari1[i]]], na.rm = TRUE)
  IQRR[[i]] <- quantile(Right[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  median_GControl[[i]] <- median(Control[[vari1[i]]], na.rm = TRUE)
  IQRControl[[i]] <- quantile(Control[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
}


table2 <- list()
table2[["ID"]] <- vari1  
table2[["IQR I"]] <- IQRI
table2[["IQR C"]] <- IQRC
table2[["IQR L"]] <- IQRL
table2[["IQR R"]] <- IQRR
table2[["IQR Control"]] <- IQRControl
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "test.csv")
