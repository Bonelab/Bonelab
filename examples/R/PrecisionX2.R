#Get LSC and RMSCV for precision scans
#run "mergeXT2precision.R" and/or "mergeXT2RegPrecision.R" to organize data
# Run on multiple outcomes
# Used in Manske et al. 2017 JBMR
# Sarah Manske
# Last updated 2017-02-15

#Sarah's setup
setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/R scripts")

#STATS
source("withinSystemLSC.R")
source("RegressionNoEqn.R")
source("BlandAltmanHorizontalNoLabel.R")

#SETTINGS FOR PLOTS
szVarName = 1
szLetter = 1.5
sz=0.9; #axis labels
szout = 1.1;
sz1=0.8; #axis numbers r
sz2=0.8 #regression labels
sz3=0.4; #Bland-Altman labels 
szPoint = 1 #size of data point

setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/Precision/XT2Results")

# #radius
# data <- read.csv("radiusX2_precision.csv")
# dataSetName <- "radiusX2"
# data <-subset(data,(Motion_P1<4 & Motion_P2<4))
# outfile <-  "X2_precision_results_exclude_motion4.csv"


#tibia
data <- read.csv("tibiaX2_precision.csv")
dataSetName <- "tibiaX2"
data <-subset(data,(Motion_P1<4 & Motion_P2<4))
outfile <-  "X2_precision_results_exclude_motion4.csv"



##############################
var = "BMD"
##############################
    varName = paste(var,"_",dataSetName,sep="")
    P1 = data$BMD_P1
    P2 = data$BMD_P2
    withinSystemLSC(P1,P2,varName,outfile)
    
    lowlim1 = 100;
    highlim1 = 500;
    ylim1=50;offset=0;
    
    file = paste(varName,".pdf",sep="")
    pdf(file)
    par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
    Regression(P1,P2,"P1","P2","",0)
    BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
    dev.off()

##############################
var = "CtBMD"
##############################
    varName = paste(var,"_",dataSetName,sep="")
    P1 = data$CtBMD_P1
    P2 = data$CtBMD_P2
    withinSystemLSC(P1,P2,varName,outfile)
    
    lowlim1 = 600;
    highlim1 = 1200;
    ylim1=100;offset=0;
    
    file = paste(varName,".pdf",sep="")
    pdf(file)
    par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
    Regression(P1,P2,"P1","P2","",0)
    BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()

##############################
var = "TbBMD"
##############################
    varName = paste(var,"_",dataSetName,sep="")
    P1 = data$TbBMD_P1
    P2 = data$TbBMD_P2
    withinSystemLSC(P1,P2,varName,outfile)
    
    lowlim1 = 50;
    highlim1 = 300;
    ylim1=40;offset=0;
    
    file = paste(varName,".pdf",sep="")
    pdf(file)
    par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
    Regression(P1,P2,"P1","P2","",0)
    BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()

##############################
var = "CtTh"
##############################
varName = paste(var,"_",dataSetName,sep="")
P1 = data$CtTh_P1
P2 = data$CtTh_P2
withinSystemLSC(P1,P2,varName,outfile)

lowlim1 = 0.5;
highlim1 = 2.5;
ylim1=0.5;offset=0;

file = paste(varName,".pdf",sep="")
pdf(file)
par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
Regression(P1,P2,"P1","P2","",0)
BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()

##############################
var = "CtPo"
##############################
varName = paste(var,"_",dataSetName,sep="")
P1 = data$CtPo_P1*100
P2 = data$CtPo_P2*100
withinSystemLSC(P1,P2,varName,outfile)

lowlim1 = 0;
highlim1 = 5;
ylim1=1.2;offset=0;

file = paste(varName,".pdf",sep="")
pdf(file)
par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
Regression(P1,P2,"P1","P2","",0)
BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()

##############################
var = "BVTV"
##############################
varName = paste(var,"_",dataSetName,sep="")
P1 = data$BVTV_P1*100
P2 = data$BVTV_P2*100
withinSystemLSC(P1,P2,varName,outfile)

lowlim1 = 0;
highlim1 = 50;
ylim1=5;offset=0;

file = paste(varName,".pdf",sep="")
pdf(file)
par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
Regression(P1,P2,"P1","P2","",0)
BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()

##############################
var = "TbN"
##############################
varName = paste(var,"_",dataSetName,sep="")
P1 = data$TbN_P1
P2 = data$TbN_P2
withinSystemLSC(P1,P2,varName,outfile)

lowlim1 = 0;
highlim1 = 2;
ylim1=0.2;offset=0;

file = paste(varName,".pdf",sep="")
pdf(file)
par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
Regression(P1,P2,"P1","P2","",0)
BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()

##############################
var = "TbTh"
##############################
varName = paste(var,"_",dataSetName,sep="")
P1 = data$TbTh_P1
P2 = data$TbTh_P2
withinSystemLSC(P1,P2,varName,outfile)

lowlim1 = 0.15;
highlim1 = 0.35;
ylim1=0.05;offset=0;

file = paste(varName,".pdf",sep="")
pdf(file)
par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
Regression(P1,P2,"P1","P2","",0)
BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()

##############################
var = "TbSp"
##############################
varName = paste(var,"_",dataSetName,sep="")
P1 = data$TbSp_P1
P2 = data$TbSp_P2
withinSystemLSC(P1,P2,varName,outfile)

lowlim1 = 0;
highlim1 = 2.0;
ylim1=0.5;offset=0;

file = paste(varName,".pdf",sep="")
pdf(file)
par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
Regression(P1,P2,"P1","P2","",0)
BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()

##############################
var = "TtAr"
##############################
varName = paste(var,"_",dataSetName,sep="")
P1 = data$TtAr_P1
P2 = data$TtAr_P2
withinSystemLSC(P1,P2,varName,outfile)

lowlim1 = 500;
highlim1 = 1000;
ylim1=50;offset=0;

file = paste(varName,".pdf",sep="")
pdf(file)
par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
Regression(P1,P2,"P1","P2","",0)
BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()

##############################
var = "CtAr"
##############################
varName = paste(var,"_",dataSetName,sep="")
P1 = data$CtAr_P1
P2 = data$CtAr_P2
withinSystemLSC(P1,P2,varName,outfile)

lowlim1 = 0;
highlim1 = 300;
ylim1=150;offset=0;

file = paste(varName,".pdf",sep="")
pdf(file)
par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
Regression(P1,P2,"P1","P2","",0)
BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()

##############################
var = "TbAr"
##############################
varName = paste(var,"_",dataSetName,sep="")
P1 = data$TbAr_P1
P2 = data$TbAr_P2
withinSystemLSC(P1,P2,varName,outfile)

lowlim1 = 300;
highlim1 = 1000;
ylim1=100;offset=0;

file = paste(varName,".pdf",sep="")
pdf(file)
par(mfrow=c(1,2),oma=c(0,4,4,6),pty='s')
Regression(P1,P2,"P1","P2","",0)
BlandAltmanHorizontal(P1,P2,paste("Mean"),"Error(P2-P1)","",varName)
dev.off()
