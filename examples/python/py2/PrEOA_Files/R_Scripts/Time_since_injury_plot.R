
# set directory
setwd("/Users/jbhatla/Documents/UofC/PrEOA/Stats/Full_ROI/")
library(data.table)
library(etable)

MF_correlation <-list()
MT_correlation <-list()
LF_correlation <-list()
LT_correlation <-list()
All_correlation <-list()
injured_correlation <-list()
contralateral_correlation <-list()
controlL_correlation <-list()
controlR_correlation <-list()
library(xtable)

# read in csv
Injured <- read.csv("Injured_participant_characteristics.csv",stringsAsFactor=F)
Injured_th <- read.csv("Measurements_Injured.csv",stringsAsFactor=F)
Contralateral_th <- read.csv("Measurements_Contralateral.csv",stringsAsFactor=F)
Left_th <- read.csv("Measurements_Left_Control.csv",stringsAsFactor=F)
Right_th <- read.csv("Measurements_Right_Control.csv",stringsAsFactor=F)
MOAKS_All <- read.csv("MOAKS_Correlations.csv",stringsAsFactor=F)

#Time since injury cart
plot(Injured$Time_since_injury, Injured_th$Th_LC_F, type='p', pch = 20, col = "red", xlab='Time Since Injury (years)', ylab='Thickness Cartilage (mm)' ,xlim=c(5, 12), ylim=c(0, 4.5), xpd=TRUE)
points(Injured$Time_since_injury, Injured_th$Th_MC_F, type='p', pch = 20, col = "green")
points(Injured$Time_since_injury, Injured_th$Th_LC_T, type='p', pch = 20, col = "blue")
points(Injured$Time_since_injury, Injured_th$Th_MC_T, type='p', pch = 20, col = "purple")
legend("topright", inset=c(-0.6,0.2), legend=c("Lateral Femur","Medial Femur", "Lateral Tibia", "Medial Tibia"), pch=c(20,20,20,20), title="Region", col = c("red", "green", "blue", "purple") )

#Time since injury bone
plot(Injured$Time_since_injury, Injured_th$Ct.Th1_LF, type='p', pch = 20, col = "red", xlab='Time Since Injury (years)', ylab='Thickness Subchondral Compact Bone (mm)' ,xlim=c(5, 12), ylim=c(0, 2.5), xpd=TRUE)
points(Injured$Time_since_injury, Injured_th$Ct.Th1_FM, type='p', pch = 20, col = "green")
points(Injured$Time_since_injury, Injured_th$Ct.Th1_LT, type='p', pch = 20, col = "blue")
points(Injured$Time_since_injury, Injured_th$Ct.Th1_MT, type='p', pch = 20, col = "purple")
legend("topright", inset=c(-0.6,0.2), legend=c("Lateral Femur","Medial Femur", "Lateral Tibia", "Medial Tibia"), pch=c(20,20,20,20), title="Region", col = c("red", "green", "blue", "purple") )

#MOAKS Injured
plot(Injured_th$MOAKS_Cart, Injured_th$Ct.Th1_LF, type='p', pch = 20, col = "red", xlab='MOAKS Cartilage Score', ylab='Thickness Subchondral Compact Bone (mm)' ,xlim=c(0, 8), ylim=c(0, 2.5), xpd=TRUE)
points(Injured_th$MOAKS_Cart, Injured_th$Ct.Th1_FM, type='p', pch = 20, col = "green")
points(Injured_th$MOAKS_Cart, Injured_th$Ct.Th1_LT, type='p', pch = 20, col = "blue")
points(Injured_th$MOAKS_Cart, Injured_th$Ct.Th1_MT, type='p', pch = 20, col = "purple")
legend("topright", inset=c(-0.6,0.2), legend=c("Lateral Femur","Medial Femur", "Lateral Tibia", "Medial Tibia"), pch=c(20,20,20,20), title="Region", col = c("red", "green", "blue", "purple") )

#MOAKS All
plot(Injured_th$MOAKS_Cart, Injured_th$Th_LC_F, type='p', pch = 20, col = "red", xlab='MOAKS Cartilage Score', ylab='Cartilage Thickness (mm)' ,xlim=c(0, 8), ylim=c(0, 4.5), xpd=TRUE)
points(Injured_th$MOAKS_Cart, Injured_th$Th_MC_F, type='p', pch = 20, col = "green")
points(Injured_th$MOAKS_Cart, Injured_th$Th_LC_T, type='p', pch = 20, col = "blue")
points(Injured_th$MOAKS_Cart, Injured_th$Th_MC_T, type='p', pch = 20, col = "purple")
legend("topright", inset=c(-0.6,0.2), legend=c("Lateral Femur","Medial Femur", "Lateral Tibia", "Medial Tibia"), pch=c(20,20,20,20), title="Region", col = c("red", "green", "blue", "purple") )

#TIBIA MOAKS All
plot(MOAKS_All$MOAKS_Cart, MOAKS_All$Th_LC_T, type='p', pch = 20, col = "red", xlab='MOAKS Cartilage Score', ylab='Cartilage Thickness (mm)' ,xlim=c(0, 8), ylim=c(0, 4.5), xpd=TRUE)
points(MOAKS_All$MOAKS_Cart, MOAKS_All$Th_MC_T, type='p', pch = 20, col = "blue")
legend("topright", inset=c(-0.6,0.2), legend=c("Lateral Tibia", "Medial Tibia"), pch=c(20,20), title="Region", col = c("red","blue") )

plot(MOAKS_All$MOAKS_Cart, MOAKS_All$Th_LC_T, type='p', pch = 20, col = "red", xlab='MOAKS Cartilage Score', ylab='Cartilage Thickness (mm)' ,xlim=c(0, 8), ylim=c(0, 4.5), xpd=TRUE)
points(MOAKS_All$MOAKS_Cart, MOAKS_All$Th_MC_T, type='p', pch = 20, col = "blue")
legend("topright", inset=c(-0.6,0.2), legend=c("Lateral Tibia", "Medial Tibia"), pch=c(20,20), title="Region", col = c("red","blue") )

#Femur MOAKS All
plot(MOAKS_All$MOAKS_Cart, MOAKS_All$Ct.Th1_LT, type='p', pch = 20, col = "red", xlab='MOAKS Cartilage Score', ylab='Subchondral Compact Bone Thickness (mm)' ,xlim=c(0, 8), ylim=c(0, 2.5), xpd=TRUE)
points(MOAKS_All$MOAKS_Cart, MOAKS_All$Ct.Th1_MT, type='p', pch = 20, col = "blue")
legend("topright", inset=c(-0.45,0.1), legend=c("Lateral Tibia","Medial Tibia"), pch=c(20,20), title="Region", col = c("red", "blue") )

#MOAKS Correlation numbers
vari1 <- c("Th_LC_F","Th_MC_F",	"Th_LC_T",	"Th_MC_T")
for(i in 1:4)
{
  injured_correlation[[i]] = cor(Injured_th$MOAKS_Cart, Injured_th[[vari1[i]]], use = "pairwise.complete.obs", method = "spearman")
  All_correlation[[i]] = cor(MOAKS_All$MOAKS_Cart, MOAKS_All[[vari1[i]]], use = "pairwise.complete.obs", method = "spearman")
  controlL_correlation[[i]] = cor(Left_th$MOAKS_Cart, Left_th[[vari1[i]]], use = "pairwise.complete.obs", method = "spearman")
  controlR_correlation[[i]] = cor(Right_th$MOAKS_Cart, Right_th[[vari1[i]]], use = "pairwise.complete.obs", method = "spearman")
  contralateral_correlation[[i]] = cor(Contralateral_th$MOAKS_Cart, Contralateral_th[[vari1[i]]], use = "pairwise.complete.obs", method = "spearman")
}


table2 <- list()
table2[["ID"]] <- vari1 
table2[["All"]] <- All_correlation
table2[["injured"]] <- injured_correlation
table2[["contralateral"]] <- contralateral_correlation
table2[["controlL"]] <- controlL_correlation
table2[["controlR"]] <- controlR_correlation
table2matrix <- do.call(rbind, table2)
table2_output <- t(table2matrix)

write.csv(table2_output, file = "MOAKS_correlations_spearman.csv")

#Boxplots
Lateral_Fem_cart_plot = boxplot(Injured_th$Th_LC_F, Contralateral_th$Th_LC_F, Left_th$Th_LC_F, Right_th$Th_LC_F, names = c("ACLR", "Contra.", "Left", "Right"), ylim=c(0.5, 3), ylab="Cartilage Thickness(mm)")
Medial_Fem_cart_plot = boxplot(Injured_th$Th_MC_F, Contralateral_th$Th_MC_F, Left_th$Th_MC_F, Right_th$Th_MC_F, names = c("ACLR", "Contra.", "Left", "Right"), ylim=c(0.5, 3))
Lateral_Tib_cart_plot = boxplot(Injured_th$Th_LC_T, Contralateral_th$Th_LC_T, Left_th$Th_LC_T, Right_th$Th_LC_T, names = c("ACLR", "Contra.", "Left", "Right"), ylim=c(1, 4.5), ylab="Cartilage Thickness(mm)")
Medial_Tib_cart_plot = boxplot(Injured_th$Th_MC_T, Contralateral_th$Th_MC_T, Left_th$Th_MC_T, Right_th$Th_MC_T, names = c("ACLR", "Contra.", "Left", "Right"), ylim=c(1, 4.5))

#Boxplots
Lateral_Fem_cart_plot = boxplot(Injured_th$Ct.Th1_LF, Contralateral_th$Ct.Th1_LF, Left_th$Ct.Th1_LF, Right_th$Ct.Th1_LF, names = c("ACLR", "Contra.", "Left", "Right"), ylim=c(0, 1.8), ylab="Subchondral Compact Bone Thickness(mm)")
Medial_Fem_cart_plot = boxplot(Injured_th$Ct.Th1_FM, Contralateral_th$Ct.Th1_FM, Left_th$Ct.Th1_FM, Right_th$Ct.Th1_FM, names = c("ACLR", "Contra.", "Left", "Right"), ylim=c(0, 1.8))
Lateral_Tib_cart_plot = boxplot(Injured_th$Ct.Th1_LT, Contralateral_th$Ct.Th1_LT, Left_th$Ct.Th1_LT, Right_th$Ct.Th1_LT, names = c("ACLR", "Contra.", "Left", "Right"), ylim=c(0, 2.5), ylab="Subchondral Compact Bone Thickness(mm)")
Medial_Tib_cart_plot = boxplot(Injured_th$Ct.Th1_MT, Contralateral_th$Ct.Th1_MT, Left_th$Ct.Th1_MT, Right_th$Ct.Th1_MT, names = c("ACLR", "Contra.", "Left", "Right"), ylim=c(0, 2.5))
