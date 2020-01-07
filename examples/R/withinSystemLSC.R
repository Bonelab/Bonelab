#withinSystemLSC Function
#Least Significant Change for 1 system 
#Ideal LSC = 2.77 * Precision Error, 
#   where 'Precision Error' is RMS SD  
#Shepherd and Lu 2007 J Clin Densitometry, ISCD Precision Calculator

#P1 is X 
#P2 is Y
#
# Used in Manske et al. 2017 JBMR
# Sarah Manske
# Last updated 2017-02-15
#
#temp
# setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/Precision")
# 
# #radius
# data <- read.csv("radiusX1_precision.csv")
# 
# 
# dataX = data$BMD_P1
# repeatX = data$BMD_P2

withinSystemLSC<-function(dataX,repeatX,varname,outFile1){
  
  #number of subjects
  n <- as.numeric(length(dataX))

  #system X
  meanX <- (dataX+repeatX)/2
  sqdif1  <- (dataX - meanX)^2
  sqdif2  <- (repeatX - meanX)^2  
  stdevX  <- sqrt((sqdif1+sqdif2))
  SumSq  <- sum(stdevX^2)
  SumSqbyN <-SumSq/n
  
  #This is called 'Precision Error' in Shepherd and Lu 2007
  RMSSD <-  sqrt(SumSqbyN)

  #LSC = 2.77 * Precision Error
  LSC <- 2.77*RMSSD

  #calculate RMS CV (Gluer 1995, by calculating individual CVsd and taking RMS average)
  #   install.packages("raster")
  library(raster)
  
  matrix <- cbind(dataX,repeatX)
  #calculate the CV for each row/participant
  indCV <- apply(matrix,1,cv)
  indCVSquare <- indCV^2
  n = length(dataX)
  sumSquare = sum(indCVSquare)
  RMSCV = sqrt(sumSquare/n)
 
  #append results to a file
  all = cbind(varname,RMSSD,LSC,RMSCV)
  if(file.exists(outFile1)) {
    write.table(all, file=outFile1, append=TRUE,row.names=FALSE,col.names=FALSE,sep=",") 
   }else {
    write.table(all, file=outFile1, append=TRUE,row.names=FALSE,col.names=TRUE,sep=",") 
  }

}
