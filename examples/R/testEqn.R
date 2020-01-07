#testEqn Function
# Sarah Manske
# last updated 2017-02-15

#####################
# Regression 
#####################
#adjXT2 <-testEqn(testVar1,coeffs[1],coeffs[2])


testEqn <-function(testVar1,intercept,slope){
  
  newY = slope*testVar1 + intercept
  

  return(newY)
  
  
  
}
