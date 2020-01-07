###################
# Bland-Altman Plot with different colour of points depending on iteration
# (e.g., for displaying results of cross-validation)
# 
# The 'sloped' option is commented out below
  # test if there is a significant slope (relationship between mean & difference)
  # if slope is significant, plot 'sloped mean & 95% LOA'
  # else plot straight lines
# Sarah Manske
# last updated 2017-02-15
###################  
BlandAltmanColour <-function(x,y,colNum){
  par(mar = c(4,3.5,0,0))
  ave=(x+y)/2
  diff=(y-x)
  points(diff~ave,
       col=colNum)
  #   abline(h=mean(diff)-c(-1.96,1.96)*sd(diff),lty=2,lwd=1.5)
  #   abline(h=mean(diff)-c(0)*sd(diff),lty=1,lwd=1.5)
  abline(h=0,col='grey',lty=1, lwd=1) 
  
  #Plot regression of diff vs average instead of horizontal line (Bland & Altman 1999)
  lm_BA = lm(diff~ave)
  info = (summary(lm_BA))
  
#   #check if slope is significant
#   slopeP = info$coefficients[2,4]
#   if(slopeP < 0.05){          #Plot sloped lines
#     print(paste(varname,"B-A Slope is Significant"))
#     
#         #Calculate 95% LOA around regression line
#         Res = residuals(lm_BA)
#         IntDA = coef(lm_BA)[1]
#         print(IntDA)
#         SlopeDA = coef(lm_BA)[2]
#         SlopeLOA = SlopeDA*ave    
#         upperLOA = IntDA + SlopeLOA +sd(Res)*1.96
#         #abline(lm(upperLOA~ave),lty=2,lwd=1.5)
#         lowerLOA = IntDA + SlopeLOA -sd(Res)*1.96
#         #abline(lm(lowerLOA~ave),lty=2,lwd=1.5)
#         
#         #use line segments (lines) instead of whole line(abline)
#         yError <-predict(lm_BA,newdata=data.frame(x=ave))
#         lines (x=ave, y=yError)
#         
#         #Upper LOA  
#         lmUpper = lm(upperLOA~ave)
#         IntUpper = coef(lmUpper)[1]
#         minX <- which.min(ave) 
#         maxX <- which.max(ave)
#         minY <- SlopeDA*ave[minX] + IntUpper
#         maxY <- SlopeDA*ave[maxX] + IntUpper
#         segments(ave[minX],minY,ave[maxX],maxY, lty=2, lwd=1)
#         
#         #Lower LOA  
#         lmLower = lm(lowerLOA~ave)
#         IntLower = coef(lmLower)[1]
#         minX <- which.min(ave) 
#         maxX <- which.max(ave)
#         minY <- SlopeDA*ave[minX] + IntLower
#         maxY <- SlopeDA*ave[maxX] + IntLower
#         segments(ave[minX],minY,ave[maxX],maxY, lty=2, lwd=1)  
#         
#         
#         #Add Subfigure labels to plot
#         legend("topleft", legend=figLetter,inset=c(-0.4,-0.08),xpd=NA,bty="n",cex=szout) 
#         #bty for box around label, xpd controls plotting region
#         
#         #Adding Labels to the Bland-Altman Plot
#         mean_lab <- substitute(paste(bar(x)) == m, 
#                                list(m = format(mean(diff), digits = 2)))
#         mean_data = mean(ave) 
#         mtext(mean_lab, side = 4, las=1, line =0.5, at=mean(diff), cex=sz3)
#     
#   } else {            #Plot straight lines
#     print(paste(varname,"B-A Slope is Not significant"))
    
        abline(h=mean(diff)-c(-1.96,1.96)*sd(diff),lty=2, lwd=1.5,col=colNum)
        abline(h=mean(diff)-c(0)*sd(diff),lty=1, lwd=1.5,col=colNum)
        #abline(h=0,col='blue',lty=2, lwd=1) 
        
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
        #       		list(t = format(mean(diff)-c(1.96)*sd(diff), digits = 3)))
        
        mean_data = mean(ave) 
#         
#         mtext(mean_lab, side = 4, las=1, line =0.5, at=mean(diff), cex=sz3)
#         mtext(conf_int_plus, side = 4, las=1, line =0.5, at=diff_plus, cex=sz3)
#         mtext(conf_int_minus, side = 4, las=1, line =0.5, at=diff_minus, cex=sz3)
# #  }
#   
#   #print(lm_BA)
#   #abline(lm(diff~ave),lwd=1.5)
#   
#   
#   #Add Subfigure labels to plot
#   legend("topleft", legend=figLetter,inset=c(-0.4,-0.08),xpd=NA,bty="n",cex=szout) 
#   #bty for box around label, xpd controls plotting region
#   
#     #Write Regression output to a file to determine significance of Slope
#     outFile='Bland-Altman Regression output.txt'
#     out <- capture.output(summary(lm_BA))
#     cat(varname,file=outFile,sep="\n", append=TRUE)
#     cat(out,file=outFile,sep="\n", append=TRUE)
  #   
}