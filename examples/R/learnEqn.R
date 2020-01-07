# learnEqn Function
# Sarah Manske
# last updated 2017-02-15

#####################
# Regression 
#####################
learnEqn <-function(x,y,varname){
  
  compare.lm = lm(y~x)
  
  
  ######################################################
  #write Regression output to a file 
  ######################################################
  
  outFile1="Regression output XT1 vs XT2.csv"
  
  b = compare.lm$coefficients[1] 
  a = compare.lm$coefficients[2]
  need = summary(compare.lm)
  SEE = need$sigma   #this is the standard error of estimate, or 'residual standard error'
  Rsquare = need$r.squared
  p = (summary(compare.lm)$coefficients[1,4])
  print(Rsquare)
  
  #check if intercept is significant, otherwise force regression through 0 (intercept = 0)
  if (p>0.05) {
    sigInt = "False"
    compare.lm <- lm(y~0+ x)
    #regression intercept
    b = 0
    #regression slope
    a = as.numeric(compare.lm$coefficients[1])
    need = summary(compare.lm)
    #rootmean square error
    SEE = need$sigma   #this is the standard error of estimate, or 'residual standard error','root-mean square error'
    Rsquare = need$r.squared
    print(Rsquare)
    
  } else {
    sigInt = "True"
  }
  
  line_eqn <- cbind(b,a)
  print(line_eqn)
  
  ave=(x+y)/2;
  diff=(y-x);
  meanAll = mean(ave);
  SEEpercent = SEE/meanAll;
  
  LOA_plus = mean(diff)+1.96*sd(diff);
  LOA_minus = mean(diff)-1.96*sd(diff);
  
#   all = cbind(varname,int, sl, SEE,SEEpercent,Rsquare,meanAll,LOA_plus,LOA_minus)
#   write.table(all, file=outFile1, append=TRUE,row.names=FALSE,sep=",")
  
  #rename variables?
  Slope       = a
  Intercept   = b
  
  #append results to a file
  all = cbind(varname,Slope,Intercept,Rsquare,p,sigInt,SEE,SEEpercent,meanAll,LOA_plus,LOA_minus)
  if(file.exists(outFile1)) {
    write.table(all, file=outFile1, append=TRUE,row.names=FALSE,col.names=FALSE,sep=",") 
  }else {
    write.table(all, file=outFile1, append=TRUE,row.names=FALSE,col.names=TRUE,sep=",") 
  }
   
  return(line_eqn)
     
  }
  


  
 