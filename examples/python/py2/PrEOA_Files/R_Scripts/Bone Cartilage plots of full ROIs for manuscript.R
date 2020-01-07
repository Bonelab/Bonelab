
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

plot(Left$Ct.Th1_LF, Left$Th_LC_F, cex=0.8, pch = 19, col=c("green"), xlab="Subchondral Compact Bone Thickness (mm)", ylab="Cartilage Thickness (mm)", xlim=c(0.2, 0.79), ylim=c(0.55, 3))
points(Right$Ct.Th1_LF, Right$Th_LC_F, cex=0.8, pch = 19, col=c("blue"))
points(Injured$Ct.Th1_LF, Injured$Th_LC_F, cex=0.8, pch = 19, col=c("red"))
points(Contralateral$Ct.Th1_LF, Injured$Th_LC_F, cex=0.8, pch = 19, col=c("orange"))
#legend(0.654, 1.69, legend=c("ACLR", "Controlateral", "Left Control", "Right Control"), col=c("red", "orange", "green", "blue"), pch = c(19,19,19,19), cex=0.8)
title(main="Lateral Femur", cex.lab=0.75)


plot(Left$Ct.Th1_FM, Left$Th_MC_F, cex=0.8, pch = 19, col=c("green"), xlab="Subchondral Compact Bone Thickness (mm)", ylab="Cartilage Thickness (mm)", xlim=c(0.2, 2), ylim=c(0.55, 3))
points(Right$Ct.Th1_FM, Right$Th_MC_F, cex=0.8, pch = 19, col=c("blue"))
points(Injured$Ct.Th1_FM, Injured$Th_MC_F, cex=0.8, pch = 19, col=c("red"))
points(Contralateral$Ct.Th1_FM, Injured$Th_MC_F, cex=0.8, pch = 19, col=c("orange"))
#legend(0.6, 2, legend=c("ACLR", "Controlateral", "Left Control", "Right Control"), col=c("red", "orange", "green", "blue"), pch = c(19,19,19,19), cex=0.8)
title(main="Medial Femur", cex.lab=0.75)

plot(Left$Ct.Th1_LT, Left$Th_LC_T, cex=0.8, pch = 19, col=c("green"), xlab="Subchondral Compact Bone Thickness (mm)", ylab="Cartilage Thickness (mm)", xlim=c(0.2, 3), ylim=c(0.55, 5))
points(Right$Ct.Th1_LT, Right$Th_LC_T, cex=0.8, pch = 19, col=c("blue"))
points(Injured$Ct.Th1_LT, Injured$Th_LC_T, cex=0.8, pch = 19, col=c("red"))
points(Contralateral$Ct.Th1_LT, Injured$Th_LC_T, cex=0.8, pch = 19, col=c("orange"))
legend(2.35, 2, legend=c("ACLR", "Controlateral", "Left Control", "Right Control"), col=c("red", "orange", "green", "blue"), pch = c(19,19,19,19), cex=0.8)
title(main="Lateral Tibia", cex.lab=0.75)

plot(Left$Ct.Th1_MT, Left$Th_MC_T, cex=0.8, pch = 19, col=c("green"), xlab="Subchondral Compact Bone Thickness (mm)", ylab="Cartilage Thickness (mm)", xlim=c(0.2, 3), ylim=c(0.55, 5))
points(Right$Ct.Th1_MT, Right$Th_MC_T, cex=0.8, pch = 19, col=c("blue"))
points(Injured$Ct.Th1_MT, Injured$Th_MC_T, cex=0.8, pch = 19, col=c("red"))
points(Contralateral$Ct.Th1_MT, Injured$Th_MC_T, cex=0.8, pch = 19, col=c("orange"))
#legend(0.6, 2, legend=c("ACLR", "Controlateral", "Left Control", "Right Control"), col=c("red", "orange", "green", "blue"), pch = c(19,19,19,19), cex=0.8)
title(main="Medial Tibia", cex.lab=0.75)