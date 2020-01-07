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
GroupH_comparison <- list()
GroupR_data <- list()
GroupL_data <- list()
GroupH_data <- list()
mean_GR <- list()
mean_GL <- list()
mean_GH <- list()


vari1 <- c("Th_LC_F",	"SD_LC_F",	"Max_LC_F",	"Th_MC_F",	"SD_MC_F",	"Max_MC_F",	"Th_LC_T",	"SD_LC_T",	"Max_LC_T",	"Th_MC_T",	"SD_MC_T",	"Max_MC_T",	"Age1",	"Ct.vBMD1_LF",	"Ct.Po1_LF",	"Ct.Th1_LF",	"Ct.vBMD1_FM",	"Ct.Po1_FM",	"Ct.Th1_FM",	"Ct.vBMD1_LT",	"Ct.Po1_LT",	"Ct.Th1_LT",	"Ct.vBMD1_MT",	"Ct.Po1_MT",	"Ct.Th1_MT")

################# Left Right Comparison  ###############
for(i in 1:24)
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
for(i in 1:24)
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
