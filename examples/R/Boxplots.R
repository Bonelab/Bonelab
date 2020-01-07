# Read in Data iMac
setwd("/Users/skboyd/Documents/pack/bonelab/trunk/examples/R-statistics")
setwd("./data")

data <-read.table("Boxplots Data.txt", header=TRUE,na.strings=".",quote="\"")

szVarname = 1.2 #Varibale title
szLabel=0.8; #axis labels
szAxis=0.7; #axis numbers 
szPoint = 0.7 #size of data point

#####################
# Box Plots
#####################
boxplot <-function(grp,y,xlab1,ylab1,title){
  #pdf(file)

  plot(y~grp, xlab=xlab1, ylab=ylab1, main=title, ylim=c(lowlim1,highlim1), pch=1 , 
       range=0.95, #wiskers 95%
       horizontal=TRUE, #Make boxplot horizontal
       boxwex=0.4, #Width of box plots
       las=1, #rotate y axis labels
       cex.main=szVarname, cex.lab=szLabel, cex.axis=szAxis)
  
  #Adding Means to the boxplots (Horizontal needs to be FALSE)
  #means <- by(y,grp,mean,na.rm=TRUE)
  #points(means,col="red",pch=19)
  
  par(mar = c(5.1,4.1,4.1,2.1)) #south, west, north, east
  
}
  

################################
# Call function to create plots:
################################

#Vitamin D (25(OH)D)
file = "VitD.pdf"
pdf(file, width = 6, height = 6)
par(oma=c(0,0,0,0),pty='s')

  lowlim1 = 0;
  highlim1 = 400;
  data$Time_point = factor(data$Time_point,c("Baseline","3M","6M","12M"))
  boxplot(data$Time_point, #X-axis data
          data$Vit_D, #y-axis data
          expression(paste("Time")), #X-axis label
          expression(paste("25(OH)D (nmol/L)")), #Y-axis label
          expression(paste("Serum Vitamin D"))) #Figure Title
dev.off()

#PTH
file = "PTH.pdf"
pdf(file, width = 6, height = 6)
par(oma=c(0,2,1,1),pty='s')

lowlim1 = 0;
highlim1 = 60;
data$Time_point = factor(data$Time_point,c("Baseline","3M","6M","12M"))
boxplot(data$Time_point, #X-axis data
        data$PTH, #y-axis data
        expression(paste("Time")), #X-axis label
        expression(paste("PTH (ng/L)")), #Y-axis label
        expression(paste("Parathyroid Hormone"))) #Figure Title

dev.off()

#ALB
file = "Albumin.pdf"
pdf(file, width = 6, height = 6)
par(oma=c(0,2,1,1),pty='s')

lowlim1 = 30;
highlim1 = 45;
data$Time_point = factor(data$Time_point,c("Baseline","3M","6M","12M"))
boxplot(data$Time_point, #X-axis data
        data$Albumin, #y-axis data
        expression(paste("Time")), #X-axis label
        expression(paste("Albumin (g/L)")), #Y-axis label
        expression(paste("Serum Albumin"))) #Figure Title

dev.off()

#Serum Calcium
file = "Calcium.pdf"
pdf(file, width = 6, height = 6)
par(oma=c(0,2,1,1),pty='s')

lowlim1 = 2.1;
highlim1 = 2.7;
data$Time_point = factor(data$Time_point,c("Baseline","3M","6M","12M"))
boxplot(data$Time_point, #X-axis data
        data$Ca, #y-axis data
        expression(paste("Time")), #X-axis label
        expression(paste("Calcium (mmol/L)")), #Y-axis label
        expression(paste("Serum Calcium"))) #Figure Title

dev.off()

#Serum CTX
file = "Serum CTX.pdf"
pdf(file, width = 6, height = 6)
par(oma=c(0,2,1,1),pty='s')

  lowlim1 = 0;
  highlim1 = 1000;
  data$Time_point = factor(data$Time_point,c("Baseline","6M","12M"))
  boxplot(data$Time_point,
          data$CTX,
          expression(paste("Month")), #X-axis label
          expression(paste("CTX ng/L")), #Y-axis label
          expression(paste("Serum CTX"))) #Figure Title
 
dev.off()


