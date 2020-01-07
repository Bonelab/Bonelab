# Read in data

# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Stats/Full_ROI/")
library(data.table)
library(etable)
library(xtable)

# read in csv
Left <- read.csv("Measurements_Left_Control.csv",stringsAsFactor=F)
Right <- read.csv("Measurements_Right_Control.csv",stringsAsFactor=F)
Injured <- read.csv("Measurements_Injured.csv",stringsAsFactor=F)
Contralateral <- read.csv("Measurements_Contralateral.csv",stringsAsFactor=F)
Control <- read.csv("Measurements_All_Control.csv",stringsAsFactor=F)

injured_correlation <-list()
contralateral_correlation <-list()
controlL_correlation <-list()
controlR_correlation <-list()

#vari1 <- c("mean_post_bone_LF",	"mean_cent_bone_LF",	"mean_ant_bone_LF",	"mean_post_bone_MF",	"mean_cent_bone_MF",	"mean_ant_bone_MF",	"mean_post_bone_LT",	"mean_ant_bone_LT",	"mean_post_bone_MT",	"mean_ant_bone_MT")
#vari2 <- c("mean_post_cart_LF",	"mean_cent_cart_LF",	"mean_ant_cart_LF",	"mean_post_cart_MF",	"mean_cent_cart_MF",	"mean_ant_cart_MF",	"mean_post_cart_LT",	"mean_ant_cart_LT",	"mean_post_cart_MT",	"mean_ant_cart_MT")
vari1 <- c("Th_LC_F","Th_MC_F",	"Th_LC_T",	"Th_MC_T")
vari2 <- c("Ct.Th1_LF",	"Ct.Th1_FM",	"Ct.Th1_LT", "Ct.Th1_MT")

for(i in 1:4)
{
  injured_correlation[[i]] = cor(Injured[[vari1[i]]], Injured[[vari2[i]]], use = "pairwise.complete.obs", method = "spearman")
  controlL_correlation[[i]] = cor(Left[[vari1[i]]], Left[[vari2[i]]], use = "pairwise.complete.obs", method = "spearman")
  controlR_correlation[[i]] = cor(Right[[vari1[i]]], Right[[vari2[i]]], use = "pairwise.complete.obs", method = "spearman")
  contralateral_correlation[[i]] = cor(Contralateral[[vari1[i]]], Contralateral[[vari2[i]]], use = "pairwise.complete.obs", method = "spearman")
}


table2 <- list()
table2[["ID"]] <- vari1  
table2[["injured"]] <- injured_correlation
table2[["contralateral"]] <- contralateral_correlation
table2[["controlL"]] <- controlL_correlation
table2[["controlR"]] <- controlR_correlation
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "bone_cart_correlations_spearman.csv")

