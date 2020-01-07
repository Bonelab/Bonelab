# Read in Data
setwd("/Users/skboyd/Documents/projects/Framingham Project/2014 Finite Element Analysis Work/Compare Axial versus Uniaxial test")
data <-read.table("Compare Axial versus Uniaxial.txt", header=T,quote="\"")

sz=1.5;
sz2=1.7;

# Regression plot
Regression <-function(x,y,xlab1,ylab1,main1,file) {
  pdf(file)
  
  plot(y~x, pch=16, xlab=xlab1, ylab=ylab1, ylim=c(0, 25000), xlim=c(0,25000), main=main1, cex.lab=sz, cex.axis=sz, cex.sub=sz, cex.main=sz2)
  segments(-25000,-25000,25000,25000,col='blue',lty=2, lwd=3)
  abline(lm(y~x))
  
  # Add Equation and r-square value to Regression Plot
  lm_eqn = function(vars){
    m = lm(vars);
    eq <- substitute(italic(y) == a + b %.% italic(x), 
                     list(a = format(coef(m)[1], digits = 2), 
                          b = format(coef(m)[2], digits = 2)))
    rsqr <-substitute(~~italic(r)^2~"="~r2, 
                      list(r2 = format(summary(m)$r.squared, digits = 3)))
    text(10000, 20000, labels = eq, cex=sz2)
    text(10000, 18000, labels = rsqr, cex=sz2)
  }
  lm_eqn(y~x)
  dev.off()
}

# Bland-Altman Plot 
BlandAltman <-function(x,y,xlab2,ylab2,main2,file){
  pdf(file)
  
  ave=(x+y)/2
  diff=(y-x)
  plot(diff~ave,pch=16,ylim=c(0,4000),xlim=c(0,25000),xlab=xlab2,ylab=ylab2,main=main2, cex.lab=sz, cex.axis=sz, cex.sub=sz, cex.main=sz2)
  abline(h=mean(diff)-c(-2,2)*sd(diff),lty=2)
  abline(h=mean(diff)-c(0)*sd(diff),lty=1)
  abline(h=0,col='blue',lty=2, lwd=3) 

  # Adding Labels to the Bland-Altman Plot
  mean_lab <- substitute(italic("Mean Difference") == m, 
                   list(m = format(mean(diff), digits = 4)))
  conf_int <-substitute(italic("Confidence Interval") == u~", "~l, 
                        list(u = format(mean(diff)-c(-2)*sd(diff), digits = 4), 
                             l = format(mean(diff)-c(2)*sd(diff), digits = 4)))
  
  text(10000,3800, labels = mean_lab, cex=sz2)
  text(10000,3500, labels = conf_int, cex=sz2)
  dev.off()
}

# Call function to create plots:
Regression(data$fz_ns1_axial,data$fz_ns1_uniaxial,"Reaction Force by Axial Test [N]","Reaction Force by Uniaxial Test [N]","Regression","Plot_ReactionForce_Regression.pdf")
BlandAltman(data$fz_ns1_uniaxial,data$fz_ns1_axial,"Mean Reaction Force [N]","Reaction Force Difference (Axial - Uniaxial) [N]","Bland-Altman","Plot_ReactionForce_BlandAltman.pdf")

#------------------------------------------------------------------------------------------------

# Regression plot
Regression <-function(x,y,xlab1,ylab1,main1,file) {
  pdf(file)
  
  plot(y~x, pch=16, xlab=xlab1, ylab=ylab1, ylim=c(0, 12000), xlim=c(0,12000), main=main1, cex.lab=sz, cex.axis=sz, cex.sub=sz, cex.main=sz2)
  segments(-12000,-12000,12000,12000,col='blue',lty=2, lwd=3)
  abline(lm(y~x))
  
  # Add Equation and r-square value to Regression Plot
  lm_eqn = function(vars){
    m = lm(vars);
    eq <- substitute(italic(y) == a + b %.% italic(x), 
                     list(a = format(coef(m)[1], digits = 2), 
                          b = format(coef(m)[2], digits = 2)))
    rsqr <-substitute(~~italic(r)^2~"="~r2, 
                      list(r2 = format(summary(m)$r.squared, digits = 3)))
    text(5000, 10000, labels = eq, cex=sz2)
    text(5000, 9000, labels = rsqr, cex=sz2)
  }
  lm_eqn(y~x)
  dev.off()
}

# Bland-Altman Plot 
BlandAltman <-function(x,y,xlab2,ylab2,main2,file){
  pdf(file)
  
  ave=(x+y)/2
  diff=(y-x)
  plot(diff~ave,pch=16,ylim=c(0,2000),xlim=c(0,12000),xlab=xlab2,ylab=ylab2,main=main2, cex.lab=sz, cex.axis=sz, cex.sub=sz, cex.main=sz2)
  abline(h=mean(diff)-c(-2,2)*sd(diff),lty=2)
  abline(h=mean(diff)-c(0)*sd(diff),lty=1)
  abline(h=0,col='blue',lty=2, lwd=3) 

  # Adding Labels to the Bland-Altman Plot
  mean_lab <- substitute(italic("Mean Difference") == m, 
                   list(m = format(mean(diff), digits = 4)))
  conf_int <-substitute(italic("Confidence Interval") == u~", "~l, 
                        list(u = format(mean(diff)-c(-2)*sd(diff), digits = 4), 
                             l = format(mean(diff)-c(2)*sd(diff), digits = 4)))
  
  text(6000,1900, labels = mean_lab, cex=sz2)
  text(6000,1700, labels = conf_int, cex=sz2)
  dev.off()
}

# Call function to create plots:
Regression(data$piz_fz_fail_axial,data$piz_fz_fail_uniaxial,"Failure Load by Axial Test [N]","Failure Load by Uniaxial Test [N]","Regression","Plot_FailureLoad_Regression.pdf")
BlandAltman(data$piz_fz_fail_uniaxial,data$piz_fz_fail_axial,"Mean Failure Load [N]","Failure Load Difference (Axial - Uniaxial) [N]","Bland-Altman","Plot_FailureLoad_BlandAltman.pdf")
