# output Function
# write (append) summary of results to a .csv file
# Sarah Manske
# last updated 2017-02-15

output <-function(x,y,varname){
  
  
  compare.lm <- lm(y~x)
  outFile1="Regression output XT2* vs XT2.csv"
  
  int = compare.lm$coefficients[1] 
  sl = compare.lm$coefficients[2]
  need = summary(compare.lm)
  SEE = need$sigma   #this is the standard error of estimate, or 'residual standard error','root-mean square error'
  Rsquare = need$r.squared
  
  ave=(x+y)/2;
  diff=(y-x);
  meanAll = mean(ave);
  SEEpercent = SEE/meanAll;
  
  meanDiff = mean(diff)
  LOA_plus = mean(diff)+1.96*sd(diff);
  LOA_minus = mean(diff)-1.96*sd(diff);
  
  #calculate RMS CV (Gluer 1995, by calculating individual CVsd and taking RMS average)
#   install.packages("raster")
    library(raster)
    
    matrix <- cbind(x,y)
    #calculate the CV for each row/participant
    indCV <- apply(matrix,1,cv)
    indCVSquare <- indCV^2
    n = length(x)
    sumSquare = sum(indCVSquare)
    RMSCV = sqrt(sumSquare/n)

  all = cbind(varname,int, sl, SEE,SEEpercent,RMSCV,Rsquare,meanAll,meanDiff,LOA_plus,LOA_minus)
  write.table(all, file=outFile1, append=TRUE,row.names=FALSE,sep=",")  
  
}

