# Read in data

# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Data_and_Reports/Complete_Reports/")
library(data.table)
library(etable)
library(xtable)

# read in csv
Group1 <- read.csv("MOAKS_Correlations.csv",stringsAsFactor=F)
LCF = cor(Group1$MOAKS_Cartilage, y=Group1$Th_LC_F, use="pairwise.complete.obs", method = c("spearman"))
LCT = cor(Group1$MOAKS_Cartilage, y=Group1$Th_LC_T, use="pairwise.complete.obs", method = c("spearman"))
MCF = cor(Group1$MOAKS_Cartilage, y=Group1$Th_MC_F, use="pairwise.complete.obs", method = c("spearman"))
MCT = cor(Group1$MOAKS_Cartilage, y=Group1$Th_MC_T, use="pairwise.complete.obs", method = c("spearman"))
year_LCF = cor(Group1$Injury_year, y=Group1$Th_LC_F, use="pairwise.complete.obs", method = c("spearman"))
year_LCT = cor(Group1$Injury_year, y=Group1$Th_LC_T, use="pairwise.complete.obs", method = c("spearman"))
year_MCF = cor(Group1$Injury_year, y=Group1$Th_MC_F, use="pairwise.complete.obs", method = c("spearman"))
year_MCT = cor(Group1$Injury_year, y=Group1$Th_MC_T, use="pairwise.complete.obs", method = c("spearman"))
year_LCF_b = cor(Group1$Injury_year, y=Group1$Ct.Th_LF, use="pairwise.complete.obs", method = c("pearson"))
year_LCT_b = cor(Group1$Injury_year, y=Group1$Ct.Th_LT, use="pairwise.complete.obs", method = c("pearson"))
year_MCF_b = cor(Group1$Injury_year, y=Group1$Ct.Th_MF, use="pairwise.complete.obs", method = c("pearson"))
year_MCT_b = cor(Group1$Injury_year, y=Group1$Ct.Th_MT, use="pairwise.complete.obs", method = c("pearson"))


