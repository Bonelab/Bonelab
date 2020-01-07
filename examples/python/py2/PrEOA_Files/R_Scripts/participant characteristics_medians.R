# Read in data

# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Stats/Full_ROI/")
library(data.table)
library(etable)
library(xtable)

# read in csv
Injured <- read.csv("Injured_participant_characteristics.csv",stringsAsFactor=F)
Control <- read.csv("Control_participant_characteristics.csv",stringsAsFactor=F)

IQRI <- list()
IQRC <- list()
shapiro <- list()
shapiro2 <- list()
sdI <- list()
vari1 <- c("Age1","BMI", "knee_cir_right", "knee_cir_left", "Time_since_injury","Age_injury", "Time_since_surgery") 
           

for(i in 1:7)
{
  #meanI[[i]] <- mean(Injured[[vari1[i]]], c(0.25, 0.5, 0.75))
  shapiro[[i]] <- shapiro.test(Control[[vari1[i]]])
  sd[[i]] = t.test(Injured[[vari1[i]]], na.rm = TRUE, paired = FALSE, var.equal = TRUE)
}

table2 <- list()
table2[["ID"]] <- vari1  
table2[["IQR I"]] <- IQRI
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "participants_injured.csv")

vari2 <- c("Age1","BMI", "knee_cir_right", "knee_cir_left") 

for(i in 1:4)
{
  IQRC[[i]] <- quantile(Control[[vari2[i]]], c(0.25, 0.5, 0.75))
  shapiro2[[i]] <- shapiro.test(Control[[vari2[i]]])
}
table2 <- list()
table2[["ID"]] <- vari1  
table2[["IQR C"]] <- IQRC
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "participants_control.csv")
