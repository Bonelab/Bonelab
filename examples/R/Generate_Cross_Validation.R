# Run statistical analysis for XT1-XT2 Calibration
# JBMR Submission Revision #2 - response to reviewer's comments
# Uses "caret" for cross-validation, based on participants from 1 time-point only
# Output is Bland-Altman plots showing different iterations of linear regression
# original analysis is shown in black
# "crossValidation" needs to be run first to generate plot; points are added by subsequent steps
#
# Sarah Manske
# 2017-01-19
#
#
# install.packages("caret", dependencies = c("Depends", "Suggests"))

library(caret)

#Sarah's setup
setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/R scripts")
#setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/SoftwareDevelopment/R")

#STATS
source("crossValidation.R")
source("output.R")
source("learnEqn.R")
source("testEqn.R")
source("BlandAltmanHorizontalMultiColour.R")


#READ IN DATA - XT1 and XT2 data merged, and subsamples generated in "mergeXT1XT2.R"
##UNREGISTERED, EXCLUDE MOTION > 3, OVERLAP < 80%
setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/FinalData/Cross-Validation")

#Radius 
radData <- read.csv("radiusM06.csv")
radTest <- read.csv("radiusM12_testsample.csv")
dataSetName <- "XT2 vs XT2*"

#Tibia
tibData <- read.csv("tibiaM06.csv")
tibTest <- read.csv("tibiaM12_testsample.csv")

#SETTINGS FOR PLOTS
szVarName = 1
szLetter = 1.5
sz=0.9; #axis labels
szout = 1.1;
sz1=0.8; #axis numbers r
sz2=0.8 #regression labels
sz3=0.4; #Bland-Altman labels 
szPoint = 1 #size of data point

#TODO - try to name variables using 'paste' (string not getting recognized as variable name)

################################
# Call function to create plots:
################################

file = paste("Figure CrossValidation ",dataSetName,".pdf",sep="")
pdf(file, width = 5, height = 8.5)
par(mfrow=c(4,2),oma=c(0,4,4,6),pty='s')

  #BMD all with the same scale
    varName = "BMD"
    varName1 = radData$BMD_XT1
    varName2 = radData$BMD_XT2
    testVar1 = radTest$BMD_XT1
    testVar2 = radTest$BMD_XT2

    lowlim1 = 100;
    highlim1 = 500;
    ylim1=55;offset=0;
   
    #Add variable name adjacent to the plot
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    mtext(expression(paste("Tt.BMD (mg HA/cm"^"3",")")), WEST<-2, line=3, cex=szVarName, outer=FALSE)
 
    varName1 = tibData$BMD_XT1
    varName2 = tibData$BMD_XT2
    testVar1 = tibTest$BMD_XT1
    testVar2 = tibTest$BMD_XT2
    
    ylim1=15;offset=0;
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

mtext(expression(paste("Radius")), side = 3,at=0.3, line=0.5, adj=0.5, cex=szVarName, outer=TRUE)
mtext(expression(paste("Tibia")), side = 3,at=0.8, line=0.5, adj=0.5, cex=szVarName, outer=TRUE)

  #BVTV
    varName = "BVTV"
    varName1 = radData$BVTV_XT1
    varName2 = radData$BVTV_XT2*100
    testVar1 = radTest$BVTV_XT1
    testVar2 = radTest$BVTV_XT2*100
    
    lowlim1 = 0;
    highlim1 = 45;
    ylim1=4;
    #Add variable name adjacent to the plot
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    mtext(expression(paste("Tb.BV/TV (%)")),  WEST<-2, line=3, cex=szVarName, outer=FALSE)
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    varName1 = tibData$BVTV_XT1
    varName2 = tibData$BVTV_XT2*100
    testVar1 = tibTest$BVTV_XT1
    testVar2 = tibTest$BVTV_XT2*100
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
  #CtTh - (XT1 vs XT2)
    varName = "CtTh"
    
    varName1 = radData$CtTh_XT1
    varName2 = radData$CtTh_XT2
    testVar1 = radTest$CtTh_XT1
    testVar2 = radTest$CtTh_XT2
    
    lowlim1 = 0.5;
    highlim1 = 2.0;
    ylim1 = 0.5;
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    mtext(expression(paste("Ct.Th (mm)")), WEST<-2, line=3, cex=szVarName, outer=FALSE)
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    varName1 = tibData$CtTh_XT1
    varName2 = tibData$CtTh_XT2
    testVar1 = tibTest$CtTh_XT1
    testVar2 = tibTest$CtTh_XT2
    
    highlim1 = 2.5;
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
  #CtPo
    varName = "CtPo"
    varName1 = radData$CtPo_XT1
    varName2 = radData$CtPo_XT2*100
    testVar1 = radTest$CtPo_XT1
    testVar2 = radTest$CtPo_XT2*100
    
    lowlim1 = 0;
    highlim1 = 8;
    ylim1 = 3.0; 
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    mtext(expression(paste("Ct.Po (%)")), WEST<-2, line=3, cex=szVarName, outer=FALSE)
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    varName1 = tibData$CtPo_XT1
    varName2 = tibData$CtPo_XT2*100
    testVar1 = tibTest$CtPo_XT1
    testVar2 = tibTest$CtPo_XT2*100
    
    lowlim1 = 0;
    highlim1 = 15;
    ylim1 = 3.0; 
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

dev.off()

##-------------------------------
##will be used in Response to Reviewers
##-------------------------------
#Supplemental Figures
file = paste("Sup Fig CrossValidation ",dataSetName," p1.pdf",sep="")
pdf(file, width=5, height=11.5)
par(mfrow=c(5,2),oma=c(0,4,4,6),pty='s')

    #BMD all with the same scale
    varName = "BMD"
    varName1 = radData$BMD_XT1
    varName2 = radData$BMD_XT2
    testVar1 = radTest$BMD_XT1
    testVar2 = radTest$BMD_XT2
    
    lowlim1 = 100;
    highlim1 = 500;
    ylim1=50;offset=0;
    
    #Add variable name adjacent to the plot
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    mtext(expression(paste("Tt.BMD (mg HA/cm"^"3",")")), WEST<-2, line=3, cex=szVarName, outer=FALSE)
    
    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    varName1 = tibData$BMD_XT1
    varName2 = tibData$BMD_XT2
    testVar1 = tibTest$BMD_XT1
    testVar2 = tibTest$BMD_XT2
    
    ylim1=15;offset=0;
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)

    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

    #Ct.BMD
    varName = "CtBMD"
    varName1 = radData$CtBMD_XT1
    varName2 = radData$CtBMD_XT2
    testVar1 = radTest$CtBMD_XT1
    testVar2 = radTest$CtBMD_XT2    

    lowlim1 = 600;
    highlim1 = 1200;
    ylim1 = 75; offset = 0;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    mtext(expression(paste("Ct.BMD (mgHA/cm"^"3",")")), WEST<-2, line=3, cex=szVarName, outer=FALSE)
    
    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

    varName1 = tibData$CtBMD_XT1
    varName2 = tibData$CtBMD_XT2
    testVar1 = tibTest$CtBMD_XT1
    testVar2 = tibTest$CtBMD_XT2    

    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

    #Tb.BMD all with the same scale
    varName = "Tb.BMD"
    varName1 = radData$TbBMD_XT1
    varName2 = radData$TbBMD_XT2
    testVar1 = radTest$TbBMD_XT1
    testVar2 = radTest$TbBMD_XT2
    
    lowlim1 = 50;
    highlim1 = 300;
    ylim1 = 20; offset = 0;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    mtext(expression(paste("Tb.BMD (mg HA/cm"^"3",")")), WEST<-2, line=3, cex=szVarName, outer=FALSE)
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

    varName1 = tibData$TbBMD_XT1
    varName2 = tibData$TbBMD_XT2
    testVar1 = tibTest$TbBMD_XT1
    testVar2 = tibTest$TbBMD_XT2

    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    mtext(expression(paste("Radius")), side = 3,at=0.3, line=0.5, adj=0.5, cex=szVarName, outer=TRUE)
    mtext(expression(paste("Tibia")), side = 3,at=0.8, line=0.5, adj=0.5, cex=szVarName, outer=TRUE)
    
  #CtTh - (XT1 vs XT2)
    varName = "CtTh"
    
    varName1 = radData$CtTh_XT1
    varName2 = radData$CtTh_XT2
    testVar1 = radTest$CtTh_XT1
    testVar2 = radTest$CtTh_XT2
    
    lowlim1 = 0.5;
    highlim1 = 2.0;
    ylim1 = 0.3;
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    mtext(expression(paste("Ct.Th (mm)")), WEST<-2, line=3, cex=szVarName, outer=FALSE)

    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    varName1 = tibData$CtTh_XT1
    varName2 = tibData$CtTh_XT2
    testVar1 = tibTest$CtTh_XT1
    testVar2 = tibTest$CtTh_XT2

    highlim1 = 2.5;
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
  #CtPo
    varName = "CtPo"
    varName1 = radData$CtPo_XT1
    varName2 = radData$CtPo_XT2*100
    testVar1 = radTest$CtPo_XT1
    testVar2 = radTest$CtPo_XT2*100
    
    lowlim1 = 0;
    highlim1 = 4.0;
    ylim1 = 2.0; 
  
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    mtext(expression(paste("Ct.Po (%)")), WEST<-2, line=3, cex=szVarName, outer=FALSE)
   
    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    lowlim1 = 0;
    highlim1 = 10.0;
    ylim1 = 3.0; 
    
    varName1 = tibData$CtPo_XT1
    varName2 = tibData$CtPo_XT2*100
    testVar1 = tibTest$CtPo_XT1
    testVar2 = tibTest$CtPo_XT2*100
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

dev.off()

file = paste("Sup Fig CrossValidation ",dataSetName," p2.pdf",sep="")
pdf(file, width = 5, height = 11.5)
par(mfrow=c(5,2),oma=c(0,4,4,6),pty='s')
  #BVTV
    varName = "BVTV"
    varName1 = radData$BVTV_XT1
    varName2 = radData$BVTV_XT2*100
    testVar1 = radTest$BVTV_XT1
    testVar2 = radTest$BVTV_XT2*100
    
    lowlim1 = 0;
    highlim1 = 45;
    ylim1=5;
  
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    mtext(expression(paste("Tb.BV/TV (%)")),  WEST<-2, line=3, cex=szVarName, outer=FALSE)

    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    varName1 = tibData$BVTV_XT1
    varName2 = tibData$BVTV_XT2*100
    testVar1 = tibTest$BVTV_XT1
    testVar2 = tibTest$BVTV_XT2*100
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)    
    #'learn' the relationship between XT1 and XT2
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

mtext(expression(paste("Radius")), side = 3,at=0.3, line=0.5, adj=0.5, cex=szVarName, outer=TRUE)
mtext(expression(paste("Tibia")), side = 3,at=0.8, line=0.5, adj=0.5, cex=szVarName, outer=TRUE)

  #Tb.N
    varName = "Tb.N"
    varName1 = radData$TbN_XT1
    varName2 = radData$TbN_XT2
    testVar1 = radTest$TbN_XT1
    testVar2 = radTest$TbN_XT2
    
    lowlim1 = 0;
    highlim1 = 3.0;
    ylim1=0.5;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    mtext(expression(paste("Tb.N (mm"^"-1",")")), WEST<-2, line=3, cex=szVarName, outer=FALSE)

    varName1 = tibData$TbN_XT1
    varName2 = tibData$TbN_XT2
    testVar1 = tibTest$TbN_XT1
    testVar2 = tibTest$TbN_XT2
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    #Tb.Th
    varName = "Tb.Th"
    varName1 = radData$TbTh_XT1
    varName2 = radData$TbTh_XT2
    testVar1 = radTest$TbTh_XT1
    testVar2 = radTest$TbTh_XT2
    lowlim1 = 0;
    highlim1 = 0.3;
    ylim1 = 0.05; offset = 0;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    mtext(expression(paste("Tb.Th (mm)")), WEST<-2, line=3, cex=szVarName, outer=FALSE)
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    varName1 = tibData$TbTh_XT1
    varName2 = tibData$TbTh_XT2
    testVar1 = tibTest$TbTh_XT1
    testVar2 = tibTest$TbTh_XT2
    lowlim1 = 0.05;
    highlim1 = 0.35;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

    #Tb.Sp
    varName = "Tb.Sp"
    varName1 = radData$TbSp_XT1
    varName2 = radData$TbSp_XT2
    testVar1 = radTest$TbSp_XT1
    testVar2 = radTest$TbSp_XT2
    
    lowlim1 = 0;
    highlim1 = 2.0;
    ylim1 = 0.3; offset = 0;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    mtext(expression(paste("Tb.Sp (mm)")), WEST<-2, line=3, cex=szVarName, outer=FALSE)  
    
    varName1 = tibData$TbSp_XT1
    varName2 = tibData$TbSp_XT2
    testVar1 = tibTest$TbSp_XT1
    testVar2 = tibTest$TbSp_XT2
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
          
dev.off()

file = paste("Sup Fig CrossValidation ",dataSetName," p3.pdf",sep="")
pdf(file, width = 5, height = 11.5)
par(mfrow=c(5,2),oma=c(0,4,4,6),pty='s')

    #TtAr - not included in standard output (when there are multiple measurements)
    varName = "TtAr"
    varName1 = radData$TtAr
    varName2 = radData$TtVol_XT2
    varName2 = varName2/(168 * 0.0607)
    testVar1 = radTest$TtAr
    testVar2 = radTest$TtVol_XT2
    testVar2 = testVar2/(168 * 0.0607)
    
    lowlim1 = 150;
    highlim1 = 475;
    ylim1 = 50.0; offset = 0;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    mtext(expression(paste("Tt.Ar (mm"^"2",")")), WEST<-2, line=3, cex=szVarName, outer=FALSE)

    varName1 = tibData$TtAr
    varName2 = tibData$TtVol_XT2
    varName2 = varName2/(168 * 0.0607)
    testVar1 = tibTest$TtAr
    testVar2 = tibTest$TtVol_XT2
    testVar2 = testVar2/(168 * 0.0607)
    lowlim1 = 400;
    highlim1 = 1200;
    ylim1 = 50.0; offset = 0;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    mtext(expression(paste("Radius")), side = 3,at=0.3, line=0.5, adj=0.5, cex=szVarName, outer=TRUE)
    mtext(expression(paste("Tibia")), side = 3,at=0.8, line=0.5, adj=0.5, cex=szVarName, outer=TRUE)
    
    
    #CtAr
    varName = "CtAr"
    varName1 = radData$CtAr_XT1
    varName2 = radData$CtAr_XT2
    testVar1 = radTest$CtAr_XT1
    testVar2 = radTest$CtAr_XT2
    
    lowlim1 = 0;
    highlim1 = 150;
    ylim1 = 20; offset = 0;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    #'learn' the relationship between XT1 and XT2
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    mtext(expression(paste("Ct.Ar (mm"^"2",")")), WEST<-2, line=3, cex=szVarName, outer=FALSE)
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    lowlim1 = 0;
    highlim1 = 200;
    ylim1 = 30; offset = 0;
    varName1 = tibData$CtAr_XT1
    varName2 = tibData$CtAr_XT2
    testVar1 = tibTest$CtAr_XT1
    testVar2 = tibTest$CtAr_XT2
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

     #Tb.Ar
    varName = "Tb.Ar"
    varName1 = radData$TbAr_XT1
    varName2 = radData$TbAr_XT2
    testVar1 = radTest$TbAr_XT1
    testVar2 = radTest$TbAr_XT2
    
    lowlim1 = 100; 
    highlim1 = 400;
    ylim1=100;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")
    
    mtext(expression(paste("Tb.Ar (mm"^"2",")")), WEST<-2, line=3, cex=szVarName, outer=FALSE)
    
    varName1 = tibData$TbAr_XT1
    varName2 = tibData$TbAr_XT2
    testVar1 = tibTest$TbAr_XT1
    testVar2 = tibTest$TbAr_XT2
    lowlim1 = 300; 
    highlim1 = 1050;
    ylim1 = 50; offset = 0;
    
    crossValidate(varName1,varName2,paste("Mean",varName),"Error (XCTII*-XCTII)",varName,dataSetName)
    
    lm_eqn <- learnEqn(varName1, varName2,paste("BMD_",dataSetName))
    coeffs=lm_eqn
    #apply equation to subset of XT1 data to get XT2 data
    adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])
    BlandAltmanColour(testVar2,adjXT2,"black")

dev.off()