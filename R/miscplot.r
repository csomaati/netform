for (user.idx in 0:37){
    jpeg(paste('../brain_scripts/user-small',user.idx,'.jpg', sep=''))
    
    user.data <- read.csv(paste('../brain_scripts/user-small', user.idx, '.csv', sep=''), header=FALSE, sep=';')
    user.matrix <- data.matrix(user.data)

    heatmap(user.matrix, scale = 'row',
            Colv=NA, Rowv=NA,margins=c(3,3),
            col=grey(seq(1,0,-1)), xlab=NA)
    dev.off()
}


## plot ecoli saved graph
library(igraph)
p <- '/mnt/ADAT/measurements-route/data/metabolic/converted/topo_all_reactions_rank.gml'
g <- read.graph(p, format='gml')
g <- read.graph('topo_trace_rank.gml', format='gml');

g <- read.graph('reaction_graph.gml', format='gml');
plot(degree.distribution(g, cumulative=TRUE), log='xy')
max(degree(g))
