# Read in Data
# laptop
setwd("/Users/Sarah/Dropbox/Research_Associate_Dropbox/Projects/Resolution_Project/Accuracy/R1")

#this data file uses the same trabecular region matched with image registration across all evaluations
#use "UCT_LIST_LH_REG_HR_TRAB.txt" for same trabecular region defined by upat evaluation for LH evaluation
#For LH evaluations, Tb.N and TbBMD were evaluated and extracted with uct_list
#BVTV_calc, TbTh_calc and TbSp_calc were calculated manually

X2LHTrab <-read.table("UCT_LIST_LH_REG_HR_TRAB_R_exclude47.txt", header=TRUE,quote="\"")
X2LHCort <-read.table("UCT_LIST_LH_REG_HR_CORT_R_exclude47.txt", header=TRUE,quote="\"")
X2Trab <-read.table("UCT_LIST_REG_X2_TRAB_R_exclude47.txt", header=TRUE,quote="\"")
X2Cort <-read.table("UCT_LIST_REG_X2_CORT_R_exclude47.txt", header=TRUE,quote="\"")
HRTrab <-read.table("UCT_LIST_REG_HR_TRAB_R_exclude47.txt", header=TRUE,quote="\"")
HRCort <-read.table("UCT_LIST_REG_HR_CORT_R_exclude47.txt", header=TRUE,quote="\"")


szout = 1.5
sz=1.2; #axis labels
sz1=0.9; #axis numbers 
sz2=0.8 #regression labels
sz3=0.7; #Bland-Altman labels
szPoint = 1 #size of data point

#####################
# Regression plot
#####################
Regression <-function(x,y,xlab1,ylab1,figLetter,varHeight){
  #pdf(file)
  
  par(mar = c(5.5,1.0, 0.5,0))
  plot(y~x, pch=16, xlab=xlab1, ylab=ylab1, ylim=c(lowlim1, highlim1), xlim=c(lowlim1,highlim1), 
       cex.lab=sz, cex.axis=sz1,cex.sub=sz, cex=szPoint,mgp=c(2.5,1,0)) 
  segments(-100,-100,2000,2000,col='blue',lty=2, lwd=1)
  abline(lm(y~x),lwd=1.5)
  
  #Add Equation and r-square value to Regression Plot
  lm_eqn = function(vars){
    m = lm(vars);
    eq <- substitute(italic(y) == a + b %.% italic(x), 
                     list(a = format(coef(m)[1], digits = 2), 
                          b = format(coef(m)[2], digits = 2)))
    rsqr <-substitute(~~italic(r)^2~"="~r2, 
                      list(r2 = format(summary(m)$r.squared, digits = 2)))
    #find good location to put labels
    xstart1 = (highlim1-lowlim1)*0.25 +lowlim1
    ystart1 = 0.95*highlim1
    ystart2 = 0.87*highlim1
    text(xstart1, ystart1, labels = eq, cex=sz2)
    text(xstart1, ystart2, labels = rsqr, cex=sz2)
    
    #Add Subfigure labels to plot
    legend("topleft", legend=figLetter,inset=c(-0.4,-0.08),xpd=NA,bty="n",cex=szout) 
              #bty for box around label, xpd controls plotting region
    
  }
  lm_eqn(y~x)
}
  
######################################################
#write Regression output to a file (including p-value)
######################################################
Stat_Regression <-function(x,y,varname){
  lm.sig = lm(y~x)
  outFile='Regression output.txt'
  
  out <- capture.output(summary(lm.sig))
  cat(varname,file=outFile,sep="\n", append=TRUE)
  cat(out,file=outFile,sep="\n", append=TRUE)
  
}

###################
# Bland-Altman Plot with 'horizontal' line (95% LOA)
# use when there is no significant relationship between mean & difference
###################  
BlandAltmanHorizontal <-function(x,y,xlab2,ylab2,figLetter,varname){
  par(mar = c(5.5,0, 0.5,0))
  ave=(x+y)/2
  diff=(y-x)
  plot(diff~ave,pch=16,ylim=c(-ylim1, ylim1),xlim=c(lowlim1,highlim1),xlab=xlab2,ylab=ylab2,
       cex.lab=sz, cex.axis=sz1, cex.sub=sz,cex=szPoint,mgp=c(2.5,1,0))
  abline(h=mean(diff)-c(-1.96,1.96)*sd(diff),lty=2, lwd=1.5)
  abline(h=mean(diff)-c(0)*sd(diff),lty=1, lwd=1.5)
  abline(h=0,col='blue',lty=2, lwd=1) 
  
  #Adding Labels to the Bland-Altman Plot
  diff_plus = mean(diff)+1.96*sd(diff)
  diff_minus = mean(diff)-1.96*sd(diff)
  
  mean_lab <- substitute(paste(bar(x)) == m, 
                         list(m = format(mean(diff), digits = 2)))
  conf_int_plus <- substitute(paste(bar(x))~"+2s="~s, 
                              list(s = format(mean(diff)-c(-1.96)*sd(diff), digits = 2))) 
  conf_int_minus <- substitute(paste(bar(x))~"-2s ="~s, 
                               list(s = format(mean(diff)-c(1.96)*sd(diff), digits = 2))) 
  
  # conf_int_minus <- substitute(paste(bar(x)," + 2s")) == t,
  #   				list(t = format(mean(diff)-c(1.96)*sd(diff), digits = 3)))
  
  mean_data = mean(ave) 
  
  mtext(mean_lab, side = 4, las=1, line =0.5, at=mean(diff), cex=sz3)
  mtext(conf_int_plus, side = 4, las=1, line =0.5, at=diff_plus, cex=sz3)
  mtext(conf_int_minus, side = 4, las=1, line =0.5, at=diff_minus, cex=sz3)

#        #temp for Tb.Th XCTII
#        mtext(mean_lab, side = 4, las=1, line =0.5, at=mean(diff), cex=sz3)
#        mtext(conf_int_plus, side = 4, las=1, line =0.5, at=diff_plus+0.01, cex=sz3)
#        mtext(conf_int_minus, side = 4, las=1, line =0.5, at=diff_minus-0.01, cex=sz3)
#    
  #Add Subfigure labels to plot
  legend("topleft", legend=figLetter,xpd=NA,bty="n",cex=szout,inset=c(-0.4,-0.1)) 
  #bty for box around label, xpd controls plotting region
}

###################
# Bland-Altman Plot with 'Sloped' (95% LOA)
# use if there is a significant relationship between mean & difference
###################  
BlandAltmanSlope <-function(x,y,xlab2,ylab2,figLetter,varname){
  par(mar = c(5.5,0, 0.5,0))
  ave=(x+y)/2
  diff=(y-x)
  plot(diff~ave,pch=16,ylim=c(-ylim1, ylim1),xlim=c(lowlim1,highlim1),xlab=xlab2,ylab=ylab2,
       cex.lab=sz, cex.axis=sz1, cex.sub=sz,cex=szPoint,mgp=c(2.5,1,0))
  #   abline(h=mean(diff)-c(-1.96,1.96)*sd(diff),lty=2,lwd=1.5)
  #   abline(h=mean(diff)-c(0)*sd(diff),lty=1,lwd=1.5)
  abline(h=0,col='blue',lty=2, lwd=1) 
  
  #Plot regression of diff vs average instead of horizontal line (Bland & Altman 1999)
  lm_BA = lm(diff~ave)
  abline(lm(diff~ave),lwd=1.5)
  #Calculate 95% LOA around regression line
  Res = residuals(lm_BA)
  IntDA = coef(lm_BA)[1]
  SlopeDA = coef(lm_BA)[2]
  SlopeLOA = SlopeDA*ave    
  upperLOA = IntDA + SlopeLOA +sd(Res)*1.96
  abline(lm(upperLOA~ave),lty=2,lwd=1.5)
  lowerLOA = IntDA + SlopeLOA -sd(Res)*1.96
  abline(lm(lowerLOA~ave),lty=2,lwd=1.5)
  #   #Write Regression output to a file to determine significance of Slope
  #   ##COMMENTED OUT BECAUSE VARNAME 'CAT' CAN'T HANDLE AN EXPRESSION (USED FOR UNITS ON PLOTS)
  #   outFile='Bland-Altman Regression output.txt'
  #   out <- capture.output(summary(lm_BA))
  #   cat(varname,file=outFile,sep="\n", append=TRUE)
  #   cat(out,file=outFile,sep="\n", append=TRUE)
  #   
  
  #Add Subfigure labels to plot
  legend("topleft", legend=figLetter,inset=c(-0.4,-0.08),xpd=NA,bty="n",cex=szout) 
  #bty for box around label, xpd controls plotting region
  
  #Adding Labels to the Bland-Altman Plot
  mean_lab <- substitute(paste(bar(x)) == m, 
                         list(m = format(mean(diff), digits = 2)))
  mean_data = mean(ave) 
  mtext(mean_lab, side = 4, las=1, line =0.5, at=mean(diff), cex=sz3)
  
  #      #temp for Tb.Th XCTII
  #      mtext(mean_lab, side = 4, las=1, line =0.5, at=mean(diff), cex=sz3)
  #      mtext(conf_int_plus, side = 4, las=1, line =0.5, at=diff_plus+0.01, cex=sz3)
  #      mtext(conf_int_minus, side = 4, las=1, line =0.5, at=diff_minus-0.01, cex=sz3)
  #  
  #     #temp for Tb.Sp XCTII
  #     mtext(mean_lab, side = 4, las=1, line =0.5, at=mean(diff), cex=sz3)
  #     mtext(conf_int_plus, side = 4, las=1, line =0.5, at=diff_plus+0.05, cex=sz3)
  #     mtext(conf_int_minus, side = 4, las=1, line =0.5, at=diff_minus-0.05, cex=sz3)
  
  #Add Subfigure labels to plot
  legend("topleft", legend=figLetter,inset=c(-0.4,-0.08),xpd=NA,bty="n",cex=szout) 
  #bty for box around label, xpd controls plotting region
}

###################
# T-test
###################  
tTest <-function(x,y,varname){
  outFile='t-test output.txt'
                      
  results = t.test (x,y, paired=TRUE)
  
  out <- capture.output(results)
  cat(varname,file=outFile,sep="\n", append=TRUE)
  cat(out,file=outFile,sep="\n", append=TRUE)
}
  

################################
# Call function to create plots:
################################
#BVTV all with the same scale
file = "Figure4_BVTV_BA_modification.pdf"
pdf(file, width = 10, height = 8)
par(mfrow=c(2,2),oma=c(0,0,3,10),pty='s')

#convert to %
HR.BVTV = HRTrab$Tb.BV.TV*100
X2.BVTV = X2Trab$Tb.BV.TV*100
X2LH.BVTV = X2LHTrab$BVTVCalc*100

  #BVTV - Gaussian/Direct
  lowlim1 = 0;
  highlim1 = 30;
  ylim1 = 7; offset = 0;
  Regression(HR.BVTV,X2.BVTV,expression(paste("HR (30 ",mu,"m)")),expression(paste("XCTII (61 ",mu,"m)")),"A)",0)
  BlandAltmanSlope(HR.BVTV,X2.BVTV,expression(paste("Mean (XCTII and HR)")),"Error (XCTII-HR)","B)",'BV/TV Direct')
    
  #BVTV - LH/Derived
  Regression(HR.BVTV,X2LH.BVTV,expression(paste("HR (30 ",mu,"m)")),expression(paste("XCTIM (82 ",mu,"m)")),"C)",0)
  BlandAltmanSlope(HR.BVTV,X2LH.BVTV,expression(paste("Mean (XCTIM and HR) ")),"Error (XCTIM-HR)","D)",'BV/TV Derived')
  #add title to plot
  mtext("BV/TV (%)", NORTH<-3, line = 0.8, adj = 0.5, outer=TRUE,cex=szout)
dev.off()

#   Stat_Regression(HR.BVTV,X2.BVTV,"BV/TV Direct")
#   tTest(HR.BVTV,X2.BVTV,"BV/TV Direct")
#   Stat_Regression(HR.BVTV,X2LH.BVTV,"BV/TV Derived")
#   tTest(HR.BVTV,X2LH.BVTV,"BV/TV Derived")

#Tb.N
file = "Figure5_TbN_BA_modification.pdf"
pdf(file, width = 10, height = 8)
par(mfrow=c(2,2),oma=c(0,0,3,10),pty='s')
  #TbN - Gaussian/Direct
  lowlim1 = 0;
  highlim1 = 2;
  ylim1 = 0.55; offset = 0;
  Regression(HRTrab$DT.Tb.N,X2Trab$DT.Tb.N,expression(paste("HR (30 ",mu,"m)")),expression(paste("XCTII (61 ",mu,"m)")),"A)",0.92)
  BlandAltmanSlope(HRTrab$DT.Tb.N,X2Trab$DT.Tb.N,expression(paste("Mean (XCTII and HR)")),"Error (XCTII-HR)","B)","Trabecular Number Direct (1/mm)")
 #TbN - Derived
  Regression(HRTrab$DT.Tb.N,X2LHTrab$DT.Tb.N,expression(paste("HR (30 ",mu,"m)")),expression(paste("XCTIM (82 ",mu,"m)")),"C)",0.92)
  BlandAltmanSlope(HRTrab$DT.Tb.N,X2LHTrab$DT.Tb.N,expression(paste("Mean (XCTIM and HR) ")),"Error (XCTIM-HR)","D)","Trabecular Number Derived (1/mm)")
  #add title to plot
  mtext(expression(paste("Tb.N (mm"^"-1",")")), NORTH<-3, line = 0.8, adj = 0.5, outer=TRUE,cex=szout)
dev.off()
#   tTest(HRTrab$DT.Tb.N,X2Trab$DT.Tb.N,"Trabecular Number Direct (1/mm)")
#   Stat_Regression(HRTrab$DT.Tb.N,X2Trab$DT.Tb.N,"Trabecular Number Direct (1/mm)")
#   tTest(HRTrab$DT.Tb.N,X2LHTrab$DT.Tb.N,"Trabecular Number Derived (1/mm)")
#   Stat_Regression(HRTrab$DT.Tb.N,X2LHTrab$DT.Tb.N,"Trabecular Number Derived (1/mm)")


#TbTh
file = "Figure6_TbTh_BA_modification.pdf"
pdf(file, width = 10, height = 8)
par(mfrow=c(2,2),oma=c(0,0,3,10),pty='s')
  #TbTh - Gaussian/Direct
  lowlim1 = 0;
  highlim1 = 0.25;
  ylim1 = 0.15; offset = 0.1;
  Regression(HRTrab$DT.Tb.Th,X2Trab$DT.Tb.Th,expression(paste("HR (30 ",mu,"m)")),expression(paste("XCTII (61 ",mu,"m)")),"A)",0.54)
  BlandAltmanHorizontal(HRTrab$DT.Tb.Th,X2Trab$DT.Tb.Th,expression(paste("Mean (XCTII and HR)")),"Error (XCTII-HR)","B)","TbThDirect")
  #TbTh - Derived
  offset = 0;
  Regression(HRTrab$DT.Tb.Th,X2LHTrab$TbThCalc,expression(paste("HR (30 ",mu,"m)")),expression(paste("XCTIM (82 ",mu,"m)")),"C)",0.54)
  BlandAltmanSlope(HRTrab$DT.Tb.Th,X2LHTrab$TbThCalc,expression(paste("Mean (XCTIM and HR) ")),"Error (XCTIM-HR)","D)","TbTh Derived")
  mtext("Tb.Th (mm)", NORTH<-3, line = 0.8, adj = 0.5, outer=TRUE,cex=szout)
dev.off()
#   tTest(HRTrab$DT.Tb.Th,X2Trab$DT.Tb.Th,"Trabecular Thickness Direct (mm)")
#   Stat_Regression(HRTrab$DT.Tb.Th,X2Trab$DT.Tb.Th,"Trabecular Thickness Direct (mm)")
#   tTest(HRTrab$DT.Tb.Th,X2LHTrab$TbThCalc,"Trabecular Thickness Derived (mm)")
#   Stat_Regression(HRTrab$DT.Tb.Th,X2LHTrab$TbThCalc,"Trabecular Thickness Derived (mm)")

#TbSp
file = "Figure7_TbSp_BA_modification.pdf"
pdf(file, width = 10, height = 8)
par(mfrow=c(2,2),oma=c(0,0,3,10),pty='s')
  #TbSp - Direct
  lowlim1 = 0;
  highlim1 = 4.0;
  ylim1 = 1.2; offset = 0;
  Regression(HRTrab$DT.Tb.Sp,X2Trab$DT.Tb.Sp,expression(paste("HR (30 ",mu,"m)")),expression(paste("XCTII (61 ",mu,"m)")),"A)",0.155)
  BlandAltmanSlope(HRTrab$DT.Tb.Sp,X2Trab$DT.Tb.Sp,expression(paste("Mean (XCTII and HR) ")),"Error (XCTII-HR)","B)","TbSp Direct")
  #TbSp - Derived
  offset = 0;
  Regression(HRTrab$DT.Tb.Sp,X2LHTrab$TbSpCalc,expression(paste("HR (30 ",mu,"m)")),expression(paste("XCTIM (82 ",mu,"m)")),"C)",0.155)
  BlandAltmanSlope(HRTrab$DT.Tb.Sp,X2LHTrab$TbSpCalc,expression(paste("Mean (XCTIM and HR) ")),"Error (XCTIM-HR)","D)","TbSp Derived")
  mtext("Tb.Sp (mm)", NORTH<-3, line = 0.8, adj = 0.5, outer=TRUE,cex=szout)
dev.off()
#   tTest(HRTrab$DT.Tb.Sp,X2Trab$DT.Tb.Sp,"Trabecular Separation Direct (mm)")
#   Stat_Regression(HRTrab$DT.Tb.Sp,X2Trab$DT.Tb.Sp,"Trabecular Separation Direct (mm)")
#   tTest(HRTrab$DT.Tb.Sp,X2LHTrab$TbSpCalc,"Trabecular Separation Derived (mm)")
#   Stat_Regression(HRTrab$DT.Tb.Sp,X2LHTrab$TbSpCalc,"Trabecular Separation Derived (mm)")

#CtPo
file = "Figure8_CtPo_BA_modification.pdf"
pdf(file, width = 10, height = 8)
par(mfrow=c(2,2),oma=c(0,0,3,10),pty='s')
#convert to %
HR.CtPo = HRCort$Ct.Po*100
X2.CtPo = X2Cort$Ct.Po*100
X2LH.CtPo = X2LHCort$Ct.Po*100
  #CtPo vs 61 um 
  lowlim1 = 0;
  highlim1 = 20;
  ylim1 = 10; offset = 0;
  Regression(HR.CtPo,X2.CtPo,expression(paste("HR (30 ",mu,"m)")),expression(paste("XCTII (61 ",mu,"m)")),"A)",0.155)
  BlandAltmanSlope(HR.CtPo,X2.CtPo,expression(paste("Mean (XCTII and HR)")),"Error (XCTII-HR)","B)","CtPo X2")
  #CtPo vs 82 um
  offset = 0;
  Regression(HR.CtPo,X2LH.CtPo,expression(paste("HR (30 ",mu,"m)")),expression(paste("XCTIM (82 ",mu,"m)")),"C)",0.155)
  BlandAltmanSlope(HR.CtPo,X2LH.CtPo,expression(paste("Mean (XCTIM and HR) ")),"Error (XCTIM-HR)","D)","CtPo X1M")
  mtext("Ct.Po (%)", NORTH<-3, line = 0.8, adj = 0.5, outer=TRUE,cex=szout)
dev.off()


#   tTest(HR.CtPo,X2.CtPo,"Cortical Porosity Direct(%)")
#   Stat_Regression(HR.CtPo,X2.CtPo,"Cortical Porosity Direct(%)")
#   tTest(HR.CtPo,X2LH.CtPo,"Cortical Porosity Derived (%)")
#   Stat_Regression(HR.CtPo,X2LH.CtPo,"Cortical Porosity Derived (%)")

# #CtTh - need to pull out of log files!
# file = "CtTh_BA_modification.pdf"
# pdf(file, width = 10, height = 8)
# par(mfrow=c(2,2),oma=c(0,0,2,7),pty='s')
# #CtTh vs 61 um 
# lowlim1 = 0;
# highlim1 = 20;
# ylim1 = 10; offset = 0;
# Regression(HRTrab$DT.Tb.Sp,X2Trab$DT.Tb.Sp,expression(paste("Ct.Th (%, HR)")),expression(paste("Ct.Th (%, XCTII)")),"A)",0.155)
# BlandAltman(HRTrab$DT.Tb.Sp,X2Trab$DT.Tb.Sp,expression(paste("Mean Ct.Th")),"Error (XCTII-HR)","B)")
# #CtTh vs 82 um
# offset = 0;
# Regression(HRTrab$DT.Tb.Sp,X2Trab$DT.Tb.Sp,expression(paste("Ct.Th (%, HR)")),expression(paste("Ct.Th (%, XCTIM)")),"C)",0.155)
# BlandAltman(HRTrab$DT.Tb.Sp,X2Trab$DT.Tb.Sp,expression(paste("Mean Ct.Th")),"Error (XCTIM-HR)","D)")
# dev.off()
# tTest(HR.CtPo,X2.CtPo,"Cortical Porosity Direct(%)")
# Stat_Regression(HR.CtPo,X2.CtPo,"Cortical Porosity Direct(%)")
# tTest(HR.CtPo,X2LH.CtPo,"Cortical Porosity Derived (%)")
# Stat_Regression(HR.CtPo,X2LH.CtPo,"Cortical Porosity Derived (%)")

#CtV
file = "CtV_BA_modification.pdf"
pdf(file, width = 10, height = 8)
par(mfrow=c(2,2),oma=c(0,0,2,7),pty='s')
#CtPo vs 61 um 
lowlim1 = 0;
highlim1 = 700;
ylim1 = 60; offset = 0;
Regression(HRCort$Ct.TV,X2Cort$Ct.TV,expression(paste("Ct.TV by HR @ 30 ",mu,"m")),expression(paste("Ct.TV by XCTII @ 61 ",mu,"m")),"A)",0.155)
BlandAltman(HRCort$Ct.TV,X2Cort$Ct.TV,expression(paste("Mean Ct.TV")),"Error (XCTII-HR)","B)")
#tTest(data$DT_TbSp_H,data$DT_TbSp_X2,"Trabecular Separation Direct (mm)")

#CtV vs 82 um
Regression(HRCort$Ct.TV,X2LHCort$Ct.TV,expression(paste("Ct.TV by HR @ 30 ",mu,"m")),expression(paste("Ct.TV by XCTIM @ 82 ",mu,"m")),"C)",0.155)
BlandAltman(HRCort$Ct.TV,X2LHCort$Ct.TV,expression(paste("Mean Ct.TV")),"Error (XCTIM-HR)","D)")
#tTest(data$DT_TbSp_H,dataDerived$TbSp_calc_LH,"Trabecular Separation Derived (mm)")
mtext("Ct.Vol mm3", NORTH<-3, line = 0.8, adj = 0.5, outer=TRUE,cex=szout)
dev.off()

#TbV
file = "TbV_BA_modification.pdf"
pdf(file, width = 10, height = 8)
par(mfrow=c(2,2),oma=c(0,0,2,7),pty='s')
#TbV vs 61 um 
lowlim1 = 0;
highlim1 = 4000;
ylim1 = 100; offset = 0;
Regression(HRTrab$Tb.TV,X2Trab$Tb.TV,expression(paste("Tb.TV by HR @ 30 ",mu,"m")),expression(paste("Tb.TV by XCTII @ 61 ",mu,"m")),"A)",0.155)
BlandAltman(HRTrab$Tb.TV,X2Trab$Tb.TV,expression(paste("Mean Tb.TV")),"Error (XCTII-HR)","B)")
#tTest(data$DT_TbSp_H,data$DT_TbSp_X2,"Trabecular Separation Direct (mm)")

#TbV vs 82 um
Regression(HRTrab$Tb.TV,X2LHTrab$Tb.TV,expression(paste("Tb.TV by HR @ 30 ",mu,"m")),expression(paste("Tb.TV by XCTIM @ 82 ",mu,"m")),"C)",0.155)
BlandAltman(HRTrab$Tb.TV,X2LHTrab$Tb.TV,expression(paste("Mean Tb.TV")),"Error (XCTIM-HR)","D)")
#tTest(data$DT_TbSp_H,dataDerived$TbSp_calc_LH,"Trabecular Separation Derived (mm)")

dev.off()


