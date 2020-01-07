# Read in data

# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Stats/Subregions/")
library(data.table)
library(etable)
library(xtable)

# read in csv
Injured <- read.csv("Side_differences_injured.csv",stringsAsFactor=F)
Control <- read.csv("Side_differences_control.csv",stringsAsFactor=F)

pairedtest <-list()
vari1 <- list()
GroupH_comparison <- list()
GroupR_data <- list()
GroupL_data <- list()
GroupH_data <- list()
mean_GR <- list()
mean_GL <- list()
mean_GH <- list()


vari1 <- c("mean_post_bone_LF",	"mean_cent_bone_LF",	"mean_ant_bone_LF",	"mean_post_cart_LF",	"mean_cent_cart_LF",	"mean_ant_cart_LF",	"mean_post_bone_MF",	"mean_cent_bone_MF",	"mean_ant_bone_MF",	"mean_post_cart_MF",	"mean_cent_cart_MF",	"mean_ant_cart_MF",	"mean_post_bone_LT",	"mean_ant_bone_LT",	"mean_post_cart_LT",	"mean_ant_cart_LT",	"mean_post_bone_MT",	"mean_ant_bone_MT",	"mean_post_cart_MT",	"mean_ant_cart_MT")

################# Control Injured Comparison  ###############
for(i in 1:20)
{
  GroupH_comparison[[i]] <- wilcox.test(Control[[vari1[i]]],Injured[[vari1[i]]], na.rm = TRUE, paired =FALSE)
  median_GI[[i]] <- median(Injured[[vari1[i]]], na.rm = TRUE)
  IQRI[[i]] <- quantile(Injured[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
  median_GControl[[i]] <- median(Control[[vari1[i]]], na.rm = TRUE)
  IQRControl[[i]] <- quantile(Control[[vari1[i]]], c(0.25, 0.5, 0.75), na.rm = TRUE)
}

GroupH_comp <- sapply(GroupH_comparison, function(x) {
  c(name = x$data.name,
    p.value = x$p.value)
})

table2 <- list()
table2[["ID"]] <- vari1  
table2[["IQR I"]] <- IQRI
table2[["IQR Control"]] <- IQRControl
table2[["GroupH P Values"]] <- GroupH_comp["p.value",]
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "Side_differences_stats.csv")