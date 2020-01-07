# Read in data

# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Data_and_Reports/Complete_Reports/")
library(data.table)
library(etable)
library(xtable)

# read in csv
Left <- read.csv("Participant_Characteristics_Injured.csv",stringsAsFactor=F)
Right <- read.csv("Participant_Characteristics_Control.csv",stringsAsFactor=F)

pairedtest <-list()
vari1 <- list()
GroupL_comparison <-list()
GroupR_comparison <-list()
GroupH_comparison <- list()
total_comparison <- list()
GroupL_data <- list()
GroupR_data <- list()
GroupH_data <- list()
total_data <- list()
GroupL_data_f <- list()
GroupR_data_f <- list()
GroupH_data_f <- list()
total_data_f <- list()
mean_GL <- list()
mean_GR <- list()
mean_GH <- list()
mean_total <- list()
mean_GL_f <- list()
mean_GR_f <- list()
mean_GH_f <- list()
mean_total_f <- list()

vari1 <- c("Age1","BMI", "Knee_circumference_right", "Knee_circumference_left")

for(i in 1:4)
{
  GroupH_comparison[[i]] <- t.test(Left[[vari1[i]]],Right[[vari1[i]]], na.rm = TRUE, paired =FALSE)
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

write.csv(table2_output, file = "participants.csv")

