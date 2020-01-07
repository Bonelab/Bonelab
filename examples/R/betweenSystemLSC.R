# betweenSystemLSC Function
#Generalized Least Significant Change (GLSC)
#Shepherd and Lu 2007 J Clin Densitometry
#for measurement on different systems
#use N, mean, SD from cross-calibration dataset for final GLSC calculation
#use precision data collected independently on each system
#make sure motion data is excluded

#old is X - XT1
#new is Y - XT2

# Sarah Manske
# Last updated 2017-02-15

betweenSystemLSC<-function(varname,dataX,repeatX,crossX,dataY,repeatY,crossY,outFile1){
  

    #Precision of each system
    #number of Precision subjects
      nX <- as.numeric(length(dataX))
      nY <- as.numeric(length(dataY))
      #calculate sd of each person, using N-1 as denominator
      #system X
      meanX <- (dataX+repeatX)/2
      sqdif1  <- (dataX - meanX)^2
      sqdif2  <- (repeatX - meanX)^2  
      stdevX  <- sqrt((sqdif1+sqdif2))
      forRMSX <- stdevX^2/nX
      CVsquareX <- ((stdevX/meanX)^2)/nX
    
      #system Y
      meanY <- (dataY+repeatY)/2
      sqdif1  <- (dataY - meanY)^2
      sqdif2  <- (repeatY - meanY)^2  
      stdevY  <- sqrt((sqdif1+sqdif2))
      forRMSY <- stdevY^2/nY
      CVsquareY <- ((stdevY/meanY)^2)/nY
      
      #RMS SD = sigma
      sigmaX = sqrt(sum(forRMSX))
      sigmaY = sqrt(sum(forRMSY))
    
      #RMS CV
      RMSCV_X = sqrt(sum(CVsquareX))
      CVperX  = 100*RMSCV_X 
      RMSCV_Y = sqrt(sum(CVsquareY))
      CVperY  = 100*RMSCV_Y              #(sigmaX/(sum(alternateX)))*100
    
    
    #Cross-Calibration
      compare.lm <- lm(crossY~crossX)
      #regression intercept
      a = as.numeric(compare.lm$coefficients[1])
      #regression slope
      b = as.numeric(compare.lm$coefficients[2])
      need = summary(compare.lm)
      #rootmean square error
      RMSE = need$sigma   #this is the standard error of estimate, or 'residual standard error','root-mean square error'
      r = sqrt(need$r.squared)
      p = (summary(compare.lm)$coefficients[1,4])
    
      print(varname)
      print(r)
      #check if intercept is significant, Force regression through 0 (intercept = 0)
  #    if (summary(compare.lm)$coefficients[1,4]>0.05) {
      if (p>0.05) {

        sigInt = "False"
        compare.lm <- lm(crossY~0+ crossX)
        #regression intercept
        a = 0
        #regression slope
        b = as.numeric(compare.lm$coefficients[1])
        need = summary(compare.lm)
        #rootmean square error
        RMSE = need$sigma   #this is the standard error of estimate, or 'residual standard error','root-mean square error'
        r = sqrt(need$r.squared) 
        print(r)
      } else {
        sigInt = "True"
      }
    
      #population mean and SD from cross-calibration dataset
        meanCrossX <- mean(crossX)
        meanCrossY <- mean(crossY)
        SX <- sd(crossX)
        SY <- sd(crossY)
        crossN <- as.numeric(length(crossX))
    
    #pieces of equation
    A = sigmaY^2;
    B = (crossN-1)/(crossN-2)
    C = SY^2*(1-r^2)
    D = 1 + 1/crossN
    E = (SX^2/crossN + (SX^2 - sigmaX^2))
    F = (crossN-1)*SX^2
    G = b^2*sigmaX^2
    
    ##with correlation coefficient
    under = A+B*C*(D + E/F) +G
    # ##without correlation coefficient
    # BCalternate = Syx
    # under = A+BCalternate*(D + E/F) + G
    
    #calculate GLSC of X to Y (recalcluate for Y to X)
    absGLSC = 1.96*sqrt(under)
    perGLSC = absGLSC/(a+b*meanCrossX)*100
    
    
    #rename variables?
    popMean_XT1 = meanCrossX
    popSD_XT1   = SX
    popMean_XT2 = meanCrossY
    popSD_XT2   = SY
    Slope       = b
    Intercept   = a
        
    #append results to a file
    all = cbind(varname,absGLSC,perGLSC,popMean_XT1,popSD_XT1,popMean_XT2,popSD_XT2,Slope,Intercept,r,p,sigInt)
    if(file.exists(outFile1)) {
      write.table(all, file=outFile1, append=TRUE,row.names=FALSE,col.names=FALSE,sep=",") 
    }else {
      write.table(all, file=outFile1, append=TRUE,row.names=FALSE,col.names=TRUE,sep=",") 
    }
    
    print(absGLSC)
}

#not sure how to calculate this?
#CV_GLSC = 