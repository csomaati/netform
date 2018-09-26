args = commandArgs(trailingOnly=TRUE)

if(length(args) < 3){
    stop('Pleas specify the two dataset and an output name\n', call.=FALSE)
}

first.path <- args[1]
second.path <- args[2]
of <- args[3]

first.name <- args[4]
second.name <- args[5]

logscale <- args[6]

pdf(file=of, height=7.5, width=8.2, paper='special')
par(mar=c(4.4,7.5,2,1))

first.data<- read.csv(first.path, header = TRUE, sep = ";", dec = ".", fill = TRUE, comment.char = "#")
second.data<- read.csv(second.path, header = TRUE, sep = ";", dec = ".", fill = TRUE, comment.char = "#")
plot(1, type="n",xlab="Stretch", ylab="",xlim=c(0,4),ylim=c(0.0001,100),cex.lab=2.8,axes=F)
if(logscale == "logscale"){
    title <- "Percentage of traces"
    ## plot(1, type="n",xlab="Stretch", ylab="",xlim=c(0,6),ylim=c(0.0001,100),log="y",cex.lab=2.8,axes=F)
## axis(1,at=c(0,1,2,3,4,5,6),label=c(0,1,2,3,4,5,6),cex.axis=2.3)
##    axis(2,at=c(10^(2),10^(1),10^(0),10^(-1),10^(-2),10^(-3),10^(-4)),label=c(expression(10^2),expression(10^1),expression(10^0),expression(10^-1),expression(10^-2),expression(10^-3),expression(10^-4)),cex.axis=2.5,las=2)
} else{
    title <- "% of hier. conform paths"
    ## plot(1, type="n",xlab="Stretch", ylab="",xlim=c(0,4),ylim=c(0.0001,100),cex.lab=2.8,axes=F)
    ## axis(2,at=c(100,80,60,40,20,0),label=c(100,80,60,40,20,0),cex.axis=2.5,las=2)
}
axis(2,at=c(100,80,60,40,20,0),label=c(100,80,60,40,20,0),cex.axis=2.5,las=2)
title(ylab=title,mgp=c(5.5,1,0),cex.lab=2.8)
axis(1,at=c(0,1,2,3,4),label=c(0,1,2,3,4),cex.axis=2.3)
box(lwd=1)

## plot(1, type="n",xlab="Stretch", ylab="",xlim=c(0,6),ylim=c(0.0001,100),log="y",cex.lab=2.8,axes=F)
## title(ylab="Percentage of traces",mgp=c(5.5,1,0),cex.lab=2.8)
## axis(1,at=c(0,1,2,3,4,5,6),label=c(0,1,2,3,4,5,6),cex.axis=2.3)
## axis(2,at=c(10^(2),10^(1),10^(0),10^(-1),10^(-2),10^(-3),10^(-4)),label=c(expression(10^2),expression(10^1),expression(10^0),expression(10^-1),expression(10^-2),expression(10^-3),expression(10^-4)),cex.axis=2.5,las=2)
## box(lwd=1)

lines(first.data$X, 100*first.data$PART/first.data$ALL,lty=1,col="black",lw=3)
points(first.data$X, 100*first.data$PART/first.data$ALL,pch=21,col="black",cex=3,bg="red",lwd=2)

lines(second.data$X, 100*second.data$PART/second.data$ALL,lty=1,col="black",lw=3)
points(second.data$X, 100*second.data$PART/second.data$ALL,pch=22,col="black",cex=3,bg="green",lwd=2)

legend("bottomleft",inset=0.01, legend=c(first.name,second.name),
       lty=c(1,1,1,1),pch=c(21,22),
       col=c("black","black"),
       pt.bg=c("red","green"),
       bty="n",cex=2.6,pt.cex=3,lw=5)

dev.off()
