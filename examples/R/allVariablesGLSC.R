#################################
# Calculate Generalized Least Significant Change for Between-System Cross-Calibration
# calls "betweenSystemLSC", based on #Shepherd and Lu 2007 J Clin Densitometry
# Run on multiple outcomes
# Used in Manske et al. 2017 JBMR
# Sarah Manske
# Last updated 2017-02-15
###################################
setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/R Scripts")
source("betweenSystemLSC.R")

# #RADIUS
# #The following datasets were collected for Precision measurements (e.g., repeat scans on same participant within a day)
# #However, different participants were used for XT1 and XT2 Precision.
# dataX1 <- read.csv("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/Precision/XT1Results/radiusX1_precision.csv")
# dataX2 <- read.csv("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/Precision/XT2Results/radiusX2_precision.csv")
# dataX1 <-subset(dataX1,(Motion_P1<4 & Motion_P2<4))
# dataX2 <-subset(dataX2,(Motion_P1<4 & Motion_P2<4))
# 
# #The following datasets were collected for Cross-Calibration 
# #Same participant scanned once on XT1, once on XT2 within a day
# crossData <- read.csv("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/FinalData/radiusM06_learnsample.csv")
# dataSetName <- "radius"

#TIBIA
#The following datasets were collected for Precision measurements (e.g., repeat scans on same participant within a day)
#However, different participants were used for XT1 and XT2 Precision.
dataX1 <- read.csv("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/Precision/XT1Results/tibiaX1_precision.csv")
dataX2 <- read.csv("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/Precision/XT2Results/tibiaX2_precision.csv")

dataX1 <-subset(dataX1,(Motion_P1<4 & Motion_P2<4))
dataX2 <-subset(dataX2,(Motion_P1<4 & Motion_P2<4))
#The following datasets were collected for Cross-Calibration 
#Same participant scanned once on XT1, once on XT2 within a day
crossData <- read.csv("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/FinalData/tibiaM06.csv")
dataSetName <- "tibia"

outfile <- ("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/GLSC/GLSC_XT1_XT2.csv")

##############################
var = "BMD"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$BMD_P1
dataY = dataX2$BMD_P1
repeatX = dataX1$BMD_P2
repeatY = dataX2$BMD_P2

#Cross-calibration data
crossX <- crossData$BMD_XT1
crossY <- crossData$BMD_XT2

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)

##############################
var = "CtBMD"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$CtBMD_P1
dataY = dataX2$CtBMD_P1
repeatX = dataX1$CtBMD_P2
repeatY = dataX2$CtBMD_P2

#Cross-calibration data
crossX <- crossData$CtBMD_XT1
crossY <- crossData$CtBMD_XT2

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)

##############################
var = "TbBMD"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$TbBMD_P1
dataY = dataX2$TbBMD_P1
repeatX = dataX1$TbBMD_P2
repeatY = dataX2$TbBMD_P2

#Cross-calibration data
crossX <- crossData$TbBMD_XT1
crossY <- crossData$TbBMD_XT2

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)


##############################
var = "CtTh"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$CtTh_P1
dataY = dataX2$CtTh_P1
repeatX = dataX1$CtTh_P2
repeatY = dataX2$CtTh_P2

#Cross-calibration data
crossX <- crossData$CtTh_XT1
crossY <- crossData$CtTh_XT2

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)

##############################
var = "CtPo"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$CtPo_P1
dataY = dataX2$CtPo_P1*100
repeatX = dataX1$CtPo_P2
repeatY = dataX2$CtPo_P2*100

#Cross-calibration data
crossX <- crossData$CtPo_XT1
crossY <- crossData$CtPo_XT2*100

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)

##############################
var = "BVTV"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$BVTV_P1
dataY = dataX2$BVTV_P1
repeatX = dataX1$BVTV_P2
repeatY = dataX2$BVTV_P2

#Cross-calibration data
crossX <- crossData$BVTV_XT1
crossY <- crossData$BVTV_XT2*100

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)

##############################
var = "TbN"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$TbN_P1
dataY = dataX2$TbN_P1
repeatX = dataX1$TbN_P2
repeatY = dataX2$TbN_P2

#Cross-calibration data
crossX <- crossData$TbN_XT1
crossY <- crossData$TbN_XT2

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)

##############################
var = "TbTh"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$TbTh_P1
dataY = dataX2$TbTh_P1
repeatX = dataX1$TbTh_P2
repeatY = dataX2$TbTh_P2

#Cross-calibration data
crossX <- crossData$TbTh_XT1
crossY <- crossData$TbTh_XT2

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)

##############################
var = "TbSp"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$TbSp_P1
dataY = dataX2$TbSp_P1
repeatX = dataX1$TbSp_P2
repeatY = dataX2$TbSp_P2

#Cross-calibration data
crossX <- crossData$TbSp_XT1
crossY <- crossData$TbSp_XT2

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)

##############################
var = "TtAr"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$TtAr_P1
dataY = dataX2$TtAr_P1
repeatX = dataX1$TtAr_P2
repeatY = dataX2$TtAr_P2

#Cross-calibration data
crossX <- crossData$TtAr
crossY <- crossData$TtVol_XT2
crossY = crossY/(168 * 0.0607)

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)

##############################
var = "CtAr"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$CtAr_P1
dataY = dataX2$CtAr_P1
repeatX = dataX1$CtAr_P2
repeatY = dataX2$CtAr_P2

#Cross-calibration data
crossX <- crossData$CtAr_XT1
crossY <- crossData$CtAr_XT2

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)

##############################
var = "TbAr"
##############################
varName = paste(var,"_",dataSetName,sep="")
#Precision Data
dataX = dataX1$TbAr_P1
dataY = dataX2$TbAr_P1
repeatX = dataX1$TbAr_P2
repeatY = dataX2$TbAr_P2

#Cross-calibration data
crossX <- crossData$TbAr_XT1
crossY <- crossData$TbAr_XT2

betweenSystemLSC(varName,dataX,repeatX,crossX,dataY,repeatY,crossY,outfile)









