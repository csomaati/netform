address <- function(pos, N){
    N*(pos[2]-1)+pos[1]
}

spiralmat <- function(vector.original){
    N = ceiling(sqrt(length(vector.original)))+1
    M = N
    # M = ceiling(length(vector.original)/N)+1

    spiral <- matrix(, nrow=N, ncol=M)

    pos <- c(floor(N/2), ceiling(M/2))
    dx <- -1
    dy <- 0
    for(v in vector.original){
        spiral[address(pos, N)] = v
        if(dx == -1 && is.na(spiral[address(c(pos[1], pos[2]+1), N)])){
            dx <- 0
            dy <- 1
        }else
        if(dx == 1 && is.na(spiral[address(c(pos[1], pos[2]-1), N)])){
            dx <- 0
            dy <- -1
        }else
        if(dy == 1 && is.na(spiral[address(c(pos[1]+1, pos[2]), N)])){
            dx <- 1
            dy <- 0
        }else
        if(dy == -1 && is.na(spiral[address(c(pos[1]-1, pos[2]), N)])){
            dx <- -1
            dy <- 0
        }

        pos <- c(pos[1]+dx, pos[2]+dy)
        
    }
    spiral
}

theme_change <- theme(
 plot.background = element_blank(),
 panel.grid.minor = element_blank(),
 panel.grid.major = element_blank(),
 panel.background = element_blank(),
 panel.border = element_blank(),
 axis.line = element_blank(),
 axis.ticks = element_blank(),
 axis.text.x = element_blank(),
 axis.text.y = element_blank(),
 axis.title.x = element_blank(),
 axis.title.y = element_blank()
)

## ============ STRETCH PLOT
library(data.table)
library(reshape)
stretch.path.internet <- '/mnt/ADAT/measurements-route/data/internet/results/loop_ex_topo_trace_filtered_dnszones_rank_stretch_ratio.csv'
stretch.path.airport <- '/mnt/ADAT/measurements-route/data/airport/results/loop_ex_topo_trace_cheapest_r2r_stretch_ratio.csv'
stretch.path.brain <- '/mnt/ADAT/measurements-route/data/brain/results/all_user_stretch_ratio.csv'
# stretch.path.metabolic <- '/mnt/ADAT/measurements-route/data/metabolic/results/loop_ex_reaction_layout_topo_all_reactions_stretch_ratio.csv'
stretch.path.metabolic <- '/mnt/ADAT/measurements-route/data/metabolic/results/loop_ex_topo_cleaned_original_trace_all_reaction_layout_stretch_ratio.csv'
stretch.path.metabolic <- '/mnt/ADAT/measurements-route/data/metabolic/results/loop_ex_topo_trace_cleaned_all_reaction_layout_stretch_ratio.csv'

internet.stretch = fread(stretch.path.internet)
airport.stretch = fread(stretch.path.airport)
brain.stretch = fread(stretch.path.brain)
metabolic.stretch = fread(stretch.path.metabolic)
stretch.merged.dt = merge(internet.stretch, brain.stretch, by='idx', all=TRUE)
stretch.merged.dt = merge(stretch.merged.dt, airport.stretch, by='idx', all=TRUE)
stretch.merged.dt = merge(stretch.merged.dt, metabolic.stretch, by='idx', all=TRUE)
setnames(stretch.merged.dt, c('idx', 'internet', 'brain', 'airport', 'metabolic'))
# stretch.merged.dt <- stretch.merged.dt[, idx:=as.character(idx)]
stretch.merged.dt.melted = melt(stretch.merged.dt, id=c('idx'))
k <- t(stretch.merged.dt)
k[which(k == 0)] = NA
colnames(k) <- k[1, ]
k = k[2:5,]

pdf("all_stretch.pdf")
barplot(k, main="Route count ratio by stretch",
        xlab="Stretch", col=c("blue","red", 'green', 'purple'),
        beside=TRUE,
        log='y',
        ylim=c(min(k, na.rm=TRUE)/2,101))
legend('topright',
       legend=rownames(k), fill=c("blue","red", 'green', 'purple'),
       col=c("blue","red", 'green', 'purple'))
grid()
box()
dev.off()
## =============================

require('data.table')
require('igraph')
require('ggplot2')

args = commandArgs(trailingOnly=TRUE)
if (length(args)<2){
    stop('Usage: hatmap graph\n', call.=FALSE)
}

heatmap.path <- args[1]
g.path <- args[2]

## heatmap.path <- '/mnt/ADAT/work/measurements-route/data/internet/results/heatmap_db.csv'
## g.path <- '/mnt/ADAT/work/measurements-route/data/internet/results/heatmap_dbtrace.gml'

## heatmap.path <- '/mnt/ADAT/measurements-route/data/internet/results/heatmap_db.csv'
## g.path <- '/mnt/ADAT/measurements-route/data/internet/results/heatmap_dbtrace.gml'

heatmap.path <- '/mnt/ADAT/measurements-route/data/airport/results/heatmap_db.csv'
g.path <- '/mnt/ADAT/measurements-route/data/airport/results/heatmap_dbtrace.gml'

 heatmap.path <- '/mnt/ADAT/measurements-route/data/brain/results/plot_user38.csv'
 g.path <- '/mnt/ADAT/measurements-route/data/brain/results/plot_user38trace.gml'
 g.path <- '/mnt/ADAT/measurements-route/data/brain/converted/topo_brain_str_map_gt_user38.gml'

g <- read.graph(g.path, format='gml')
heatmap.db <- fread(heatmap.path, sep=';')
## setnames(heatmap.db, c('NODE','CLOSENESS','X', 'Y', 'SH','REAL','VFREAL','RANDOMSH'))

MINALL <- min(min(heatmap.db$REAL), min(heatmap.db$RANDOMSH))
MAXALL <- max(max(heatmap.db$REAL), max(heatmap.db$RANDOMSH))
heatmap.db.ordered <- heatmap.db[match(V(g)$name, NODE),]
heatmap.db.closenessordered <- heatmap.db[order(-CLOSENESS)]
heatmap.db.cleaned <- heatmap.db.closenessordered[RANDOMSH > 0 | REAL > 0, ]

# ggplot(heatmap.db.ordered, aes(x = V2, y = 1, fill = V3)) + geom_tile() + scale_fill_gradient(low='white', high='steelblue')
# require('plotly')
# plot_ly(z=heatmap.db.ordered$V5, x=heatmap.db.ordered$V3, y=heatmap.db.ordered$V4, type='heatmap')

colorfunc = colorRamp(c("green","yellow","red"))
w = heatmap.db.ordered$REAL

pdf("real_stretched_graph.pdf")
plot(g, vertex.label=NA, layout=as.matrix(heatmap.db.ordered[, X,Y, ]),
     vertex.size=w/50,
     vertex.color= rgb(colorfunc((w - min(w)) / (max(w) - min(w)))/255),
     edge.color=rgb(0.02,0.1,0.02,.1))
dev.off()

heatmatrix <- spiralmat(heatmap.db.cleaned$RANDOMSH)
cols2 <- colorRampPalette(c("#FFFFD4", "#FED98E", "#FE9929", "#D95F0E", "#993404"),space="Lab")(256)
pdf("internet_simple_filtered_randomsh_heatmatrix.pdf")
image(as.matrix(heatmatrix), col=cols2)
dev.off()

library(reshape2)
library(ggplot2)
myPalette <- colorRampPalette(rev(brewer.pal(11, "Spectral")), space="Lab")
heatmatrix <- spiralmat(heatmap.db.cleaned$REAL) - spiralmat(heatmap.db.cleaned$RANDOMSH)
heatmatrix[!is.finite(heatmatrix)] <- 0
melted <- melt(heatmatrix)
f <- colorRampPalette(c('blue', 'black', 'green', 'orange', 'red'))(length(unique(melted$value)))
f <- colorRampPalette(c('blue', 'black'))(23)
f <- c(f, colorRampPalette(c('green', 'orange', 'red'))(59))
# colorpalette <- colorRampPalette(c('blue', 'brown', 'yellow', 'orange', 'red'))(82)
colorpalette <- f
colorpalette[24] = '#FFFFFF'
pdf("internet_filtered_merged_heatmatrix_ggplot.pdf")
plot <- ggplot(data=melted, aes(x=Var1, y=Var2, fill=value))
plot <- plot + scale_fill_gradientn(colors=colorpalette)
plot <- plot + geom_tile(show.legend=FALSE)
plot <- plot + theme_change
print(plot)
dev.off()
