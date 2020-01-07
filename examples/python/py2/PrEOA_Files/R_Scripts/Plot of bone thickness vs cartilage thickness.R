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

#Injured Only
plot(Injured$mean_post_bone_LF, Injured$mean_post_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"), xlab="Subchondral Compact Bone Thickness", ylab="Cartilage Thickness", xlim=c(0.45, 0.9), ylim=c(0.55, 3))
points(Injured$mean_cent_bone_LF, Injured$mean_cent_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Injured$mean_ant_bone_LF, Injured$mean_ant_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))

#Control Only
plot(Left$mean_post_bone_LF, Left$mean_post_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"), xlab="Subchondral Compact Bone Thickness", ylab="Cartilage Thickness", xlim=c(0.45, 0.9), ylim=c(0.55, 3))
points(Left$mean_post_bone_LF, Left$mean_post_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Left$mean_cent_bone_LF, Left$mean_cent_cart_LF, cex=.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Left$mean_ant_bone_LF, Left$mean_ant_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Right$mean_post_bone_LF, Right$mean_post_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Right$mean_cent_bone_LF, Right$mean_cent_cart_LF, cex=.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Right$mean_ant_bone_LF, Right$mean_ant_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
#Contralateral Only
plot(Contralateral$mean_post_bone_LF, Contralateral$mean_post_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"), xlab="Subchondral Compact Bone Thickness", ylab="Cartilage Thickness", xlim=c(0.45, 0.9), ylim=c(0.55, 3))
points(Contralateral$mean_cent_bone_LF, Contralateral$mean_cent_cart_LF, cex=.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Contralateral$mean_ant_bone_LF, Contralateral$mean_ant_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))

#Left Only
plot(Left$mean_post_bone_LF, Left$mean_post_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"), xlab="Subchondral Compact Bone Thickness", ylab="Cartilage Thickness", xlim=c(0.45, 0.7), ylim=c(0.55, 3))
points(Left$mean_cent_bone_LF, Left$mean_cent_cart_LF, cex=.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Left$mean_ant_bone_LF, Left$mean_ant_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))

#Injured and Controls LF
plot(Left$mean_post_bone_LF, Left$mean_post_cart_LF, cex=0.8, pch = 5, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"), xlab="Subchondral Compact Bone Thickness (mm)", ylab="Cartilage Thickness (mm)", xlim=c(0.5, 0.82), ylim=c(0.55, 3))
points(Left$mean_cent_bone_LF, Left$mean_cent_cart_LF, cex=.8, pch = 5, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Left$mean_ant_bone_LF, Left$mean_ant_cart_LF, cex=0.8, pch = 5, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Right$mean_post_bone_LF, Right$mean_post_cart_LF, cex=0.8, pch = 5, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Right$mean_cent_bone_LF, Right$mean_cent_cart_LF, cex=.8, pch = 5, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Right$mean_ant_bone_LF, Right$mean_ant_cart_LF, cex=0.8, pch = 5, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Injured$mean_post_bone_LF, Injured$mean_post_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Injured$mean_cent_bone_LF, Injured$mean_cent_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
points(Injured$mean_ant_bone_LF, Injured$mean_ant_cart_LF, cex=0.8, pch = 19, col=c("red","blue","green","purple","orange","black","darkgrey","deeppink","aquamarine","coral3","cornflowerblue","cyan","darkolivegreen1", "gold4","forestgreen"))
legend(0.774, 1.01, legend=c("ACLR", "Control"), col=c("black", "black"), pch = c(19,5), cex=0.8)
title(main="Lateral Femur Cartilage Thickness Compared to Subchondral Compact Bone Thickness", cex.lab=0.75)
