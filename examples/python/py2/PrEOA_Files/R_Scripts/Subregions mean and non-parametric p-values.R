# Read in data

# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Stats/Subregions/")
library(data.table)
library(etable)
library(xtable)

# read in csv
Left <- read.csv("Measurements_Subregions_Control_Left.csv",stringsAsFactor=F)
Right <- read.csv("Measurements_Subregions_Control_Right.csv",stringsAsFactor=F)
Injured <- read.csv("Measurements_Subregions_Injured.csv",stringsAsFactor=F)
Contralateral <- read.csv("Measurements_Subregions_Contralateral.csv",stringsAsFactor=F)
Control <- read.csv("Measurements_Subregions_Control_All.csv",stringsAsFactor=F)

pairedtest <-list()
vari1 <- list()
GroupH_comparison <- list()
GroupR_data <- list()
GroupL_data <- list()
GroupH_data <- list()
mean_GR <- list()
mean_GL <- list()
mean_GH <- list()


vari1 <- c("mean_cent_bone_LF",	"mean_post_bone_LF",	"mean_ant_bone_LF",	"mean_cent_cart_LF",	"mean_post_cart_LF",	"mean_ant_cart_LF",	"mean_cent_bone_MF",	"mean_post_bone_MF",	"mean_ant_bone_MF",	"mean_cent_cart_MF",	"mean_post_cart_MF",	"mean_ant_cart_MF",	"mean_post_bone_LT",	"mean_ant_bone_LT",	"mean_post_cart_LT",	"mean_ant_cart_LT",	"mean_post_bone_MT",	"mean_ant_bone_MT",	"mean_post_cart_MT",	"mean_ant_cart_MT")

################# Left Right Comparison  ###############
for(i in 1:20)
{
  GroupH_comparison[[i]] <- wilcox.test(Left[[vari1[i]]],Right[[vari1[i]]], na.rm = TRUE, paired =TRUE)
  GroupL_data[[i]] <- t.test(Left[[vari1[i]]], na.rm = TRUE, paired = FALSE, var.equal = TRUE)#  GroupI_data_f[[i]] <- t.test(A_followup[[vari1[i]]], na.rm = TRUE, paired = FALSE, var.equal = TRUE)
  mean_GL[[i]] <- mean(Left[[vari1[i]]], na.rm = TRUE)
  GroupR_data[[i]] <- t.test(Right[[vari1[i]]], na.rm = TRUE, paired = FALSE, var.equal = TRUE)
  mean_GR[[i]] <- mean(Right[[vari1[i]]], na.rm = TRUE)
}

GroupH_comp <- sapply(GroupH_comparison, function(x) {
  c(name = x$data.name,
    p.value = x$p.value)
})

GroupL_data_res <- sapply(GroupL_data, function(x) {
  c(name = x$data.name,
    ci.lower = x$conf.int,
    ci.upper = x$conf.int)
})


GroupR_data_res <- sapply(GroupR_data, function(x) {
  c(name = x$data.name,
    ci.lower = x$conf.int,
    ci.upper = x$conf.int)
})


table2 <- list()
table2[["ID"]] <- vari1
table2[["Mean L Baseline"]] <- mean_GL
table2[["L CI up"]] <- GroupL_data_res["ci.lower1",]
table2[["L CI low"]] <- GroupL_data_res["ci.lower2",]
table2[["Mean R Baseline"]] <- mean_GR
table2[["R CI up"]] <- GroupR_data_res["ci.lower1",]
table2[["R CI low"]] <- GroupR_data_res["ci.lower2",]
table2[["GroupH P Values"]] <- GroupH_comp["p.value",]
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "Left_Right.csv")

################# Contralateral Injured Comparison  ###############
for(i in 1:20)
{
  GroupH_comparison[[i]] <- wilcox.test(Injured[[vari1[i]]],Contralateral[[vari1[i]]], na.rm = TRUE, paired =TRUE)
  GroupL_data[[i]] <- t.test(Injured[[vari1[i]]], na.rm = TRUE, paired = FALSE, var.equal = TRUE)#  GroupI_data_f[[i]] <- t.test(A_followup[[vari1[i]]], na.rm = TRUE, paired = FALSE, var.equal = TRUE)
  mean_GL[[i]] <- mean(Injured[[vari1[i]]], na.rm = TRUE)
  GroupR_data[[i]] <- t.test(Contralateral[[vari1[i]]], na.rm = TRUE, paired = FALSE, var.equal = TRUE)
  mean_GR[[i]] <- mean(Contralateral[[vari1[i]]], na.rm = TRUE)
}

GroupH_comp <- sapply(GroupH_comparison, function(x) {
  c(name = x$data.name,
    p.value = x$p.value)
})

GroupL_data_res <- sapply(GroupL_data, function(x) {
  c(name = x$data.name,
    ci.lower = x$conf.int,
    ci.upper = x$conf.int)
})


GroupR_data_res <- sapply(GroupR_data, function(x) {
  c(name = x$data.name,
    ci.lower = x$conf.int,
    ci.upper = x$conf.int)
})


table2 <- list()
table2[["ID"]] <- vari1
table2[["Mean L Baseline"]] <- mean_GL
table2[["L CI up"]] <- GroupL_data_res["ci.lower1",]
table2[["L CI low"]] <- GroupL_data_res["ci.lower2",]
table2[["Mean R Baseline"]] <- mean_GR
table2[["R CI up"]] <- GroupR_data_res["ci.lower1",]
table2[["R CI low"]] <- GroupR_data_res["ci.lower2",]
table2[["GroupH P Values"]] <- GroupH_comp["p.value",]
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "Injured_Contralateral.csv")
