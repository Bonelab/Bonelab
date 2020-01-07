# crossValidate Function
# Sarah Manske
# last updated 2017-02-15
#
# install.packages("caret", dependencies = c("Depends", "Suggests"))
#
#
# library(caret)
#
# #uses source scripts
# setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/R scripts")
# source("testEqn.R")
# source("BlandAltmanHorizontalMultiColour.R")
# 
# 
# #read in the data file and rename it
# setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/FinalData")
# myData <- read.csv(file="tibiaM06_learnsample.csv")
# 
# setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Cross-Calibration/FinalData/Cross-Validation")
# write.csv(myData,file="tibiaM06.csv")

crossValidate <-  function(varName1,varName2,xlab2,ylab2,varname,dataSetName){
    output  <- data.frame(Intercept=double(),Slope=double(), RMSE=double(), rsquare=double(), 
                          p=double(),SigInt=character())
    
    # #inputs for BlandAltmanHorizontal
    # dataSetName <- "XT2 vs XT2*"
    # varName     <- "CtPo"
    # lowlim1 = 0;
    # highlim1 = 8.0;
    # ylim1 = 2.0; 
    # 
    # xlab2 = paste("Mean",varName)
    # ylab2 = "Error (XCTII*-XCTII)"
    
    plot(varName1,varName2,type = "n",ylim=c(-ylim1, ylim1),xlim=c(lowlim1,highlim1),xlab=xlab2,ylab=ylab2,
         cex.lab=sz, cex.axis=sz1, cex.sub=sz,cex=szPoint,mgp=c(1.5,0.5,0))
    
    myData  <- cbind(varName1,varName2)
    partition <- as.data.frame(myData)

    for (i in 1:5){
      int = 0; slope = 0; RMSE = 0; rsquare = 0; p = 0; sigInt = 0;
      set.seed(i)
      inTrain <- createDataPartition(y=partition$varName1, p = 0.5, list=FALSE)
      str(inTrain)
      
      training  <- partition[ inTrain,]
      testing   <- partition[-inTrain,]
    
      #training
        y = training$varName2
        x = training$varName1
        
        lmRegress <- lm(y ~ x)
        
        p = (summary(lmRegress)$coefficients[1,4])
        
        #check if intercept is significant, otherwise force regression through 0 (intercept = 0)
        if (p>0.05) {
          sigInt = "False"
          lmRegress <- lm(y~0+ x)
          slope   <- coef(lmRegress)[1]
        } else {
          int   <- coef(lmRegress)[1]
          slope <- coef(lmRegress)[2]
          sigInt = "True"
        }
        
      
        need = summary(lmRegress)
        RMSE = need$sigma   #this is the standard error of estimate, or 'residual standard error','root-mean square error'
        rsquare = sqrt(need$r.squared)
        p = (summary(lmRegress)$coefficients[1,4]) #this is the significance of the "final" intercept (might be 0)
        
        sumStat <- cbind(int, slope, RMSE, rsquare, p, sigInt)
        
        output  <- rbind(output,sumStat)
      
      #testing
        testY = testing$varName2
        testX = testing$varName1
        
        adjXT2 <-testEqn(testX,int,slope)
        
        temp = i + 1; #avoid using black as the first colour on Bland-Altman
        BlandAltmanColour(testY,adjXT2,temp)
        
        
    }
    outFile1 = paste(varname, "_cross_validate.csv")
    write.table(output, file=outFile1, append=TRUE,row.names=FALSE,sep=",")  
    
}

