start.image <- function(name, ispng=FALSE){
    if (ispng){tp <- '.png'}
    else {tp <- '.pdf'}
    tp
    fname <- paste("./", name, tp, sep="" )
    if (ispng){png(fname)}
    else{pdf(fname)}
    fname
}

end.image <- function(){
    dev.off()
}

library('data.table')
a <- fread('data/foodweb/results/path_prediction_loop_ex_route_counts', sep=' ')
a <- a[order(rank(V1))]

vf.ecdf <- ecdf(1-a$V2/a$V1)
lp.ecdf <- ecdf(1-a$V3/a$V1)
lpall.ecdf <- ecdf(1-a$V3/a$V1)
r <- range(1-a$V3/a$V1)

start.image('path-prediction-loop-ex', FALSE)
curve(1-vf.ecdf(x), from=r[1], to=r[2], col="red", xlim=r, xlab='%', ylab='throwed at least in %')
curve(1-lp.ecdf(x), from=r[1], to=r[2], col="blue", xlim=r, add=TRUE)
curve(1-lpall.ecdf(x), from=r[1], to=r[2], col="green", xlim=r, add=TRUE)
legend('bottomleft', legend=c('VF', 'LP', 'LP_all'), col=c('red', 'blue', 'green'), lty=c(1,1,1))
end.image()

a <- fread('data/foodweb/results/stretch_results', sep=' ')
a <- a[order(rank(V1))]
mean(a$V1/a$V2)
mean(a$V3/a$V2)
mean(a$V4/a$V2)
mean(a$V5/a$V2)
